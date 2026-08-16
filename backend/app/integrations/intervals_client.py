import base64
import httpx
import asyncio
from typing import Dict, Any, Optional

from datetime import date, timedelta

class IntervalsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://intervals.icu/api/v1/athlete/0"

    def _get_headers(self) -> Dict[str, str]:
        token = base64.b64encode(f"API_KEY:{self.api_key}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    async def fetch_full_dataset(self) -> Dict[str, Any]:
        headers = self._get_headers()
        today = date.today()
        s42 = (today - timedelta(days=42)).isoformat()
        s365 = (today - timedelta(days=365)).isoformat()
        s_future = (today + timedelta(days=180)).isoformat()
        
        urls = {
            "athlete": self.base_url,
            "wellness": f"{self.base_url}/wellness?oldest={s365}",
            "activities_year": f"{self.base_url}/activities?oldest={s365}",
            "pc_run_42d": f"{self.base_url}/pace-curves?oldest={s42}",
            "pc_run_year": f"{self.base_url}/pace-curves?oldest={s365}",
            "pc_bike_42d": f"{self.base_url}/power-curves?oldest={s42}&type=Ride",
            "pc_bike_year": f"{self.base_url}/power-curves?oldest={s365}&type=Ride",
            "events": f"{self.base_url}/events?oldest={s365}&newest={s_future}"
        }

        async with httpx.AsyncClient(timeout=45) as client:
            res = await asyncio.gather(*[client.get(u, headers=headers) for u in urls.values()])
            
        return dict(zip(urls.keys(), [r.json() if r.status_code == 200 else None for r in res]))
        
    async def get_wellness(self, start_date: str, end_date: str) -> list[Dict[str, Any]]:
        """Fetch wellness data for a specific date range."""
        headers = self._get_headers()
        url = f"{self.base_url}/wellness?oldest={start_date}&newest={end_date}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                return res.json()
            return []

    async def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Creates a planned workout/event in Intervals.icu."""
        headers = self._get_headers()
        url = f"{self.base_url}/events"
        
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, headers=headers, json=event_data)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"Błąd tworzenia eventu w Intervals: {res.text}")
                return None

    async def delete_event(self, event_id: str) -> bool:
        """Deletes an event from Intervals.icu calendar."""
        headers = self._get_headers()
        url = f"{self.base_url}/events/{event_id}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.delete(url, headers=headers)
            return res.status_code in (200, 204)

    async def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing event in Intervals.icu."""
        headers = self._get_headers()
        url = f"{self.base_url}/events/{event_id}"

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.put(url, headers=headers, json=event_data)
            if res.status_code in (200, 201):
                return res.json()
            else:
                print(f"Błąd aktualizacji eventu w Intervals: {res.text}")
                return None

    async def clean_and_push_events(
        self,
        events_to_create: list[Dict[str, Any]],
        tag: str = "[Kowalski]"
    ) -> list[Dict[str, Any]]:
        """
        Usuwa z kalendarza poprzednie eventy z tagiem `tag` w oknie czasowym tworzonych eventów,
        a następnie dodaje nowe.
        """
        if not events_to_create:
            return []

        dates = [e.get("start_date_local", "")[:10] for e in events_to_create if e.get("start_date_local")]
        if not dates:
            return []

        earliest_date = min(dates)
        latest_date = max(dates)

        # Pobierz istniejące eventy z okna
        existing_events = await self.get_events(earliest_date, latest_date)
        if existing_events:
            to_delete = [
                e for e in existing_events
                if isinstance(e, dict) and e.get("id") and (
                    tag in (e.get("description") or "") or
                    tag in (e.get("name") or "")
                )
            ]
            for old_ev in to_delete:
                await self.delete_event(str(old_ev["id"]))

        created = []
        for ev in events_to_create:
            res = await self.create_event(ev)
            if res:
                created.append(res)
        return created

    async def get_events(self, start_date: str, end_date: str) -> list[Dict[str, Any]]:
        """Pobiera zaplanowane treningi (Events) w zadanym oknie czasowym (włączając pełną strukturę ćwiczeń)"""
        headers = self._get_headers()
        url = f"{self.base_url}/events?oldest={start_date}&newest={end_date}"
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    events = res.json()
                    return events if isinstance(events, list) else []
                return []
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    async def get_activities(self, start_date: str, end_date: str) -> list[Dict[str, Any]]:
        """Pobiera wylistowanie wykonanych treningów (Activities) w zadanym oknie czasowym z podstawowymi danymi (m.in icu_tss)"""
        headers = self._get_headers()
        url = f"{self.base_url}/activities?oldest={start_date}&newest={end_date}"
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    activities = res.json()
                    return activities if isinstance(activities, list) else []
                return []
        except Exception as e:
            print(f"Error fetching activities: {e}")
            return []

    async def get_activity_detail(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera dokładne szczegóły po ID wykonanej aktywności (np. pełne lapsy, szczegóły stref)."""
        headers = self._get_headers()
        url = f"{self.base_url}/activities/{activity_id}"
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.json()
                return None
        except Exception as e:
            print(f"Error fetching activity details: {e}")
            return None


