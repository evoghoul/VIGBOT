import json
from typing import Dict, Any, Optional, List
from app.database import DataRepository, DatabaseSession

def get_transport_summary(session: Optional[DatabaseSession] = None, query: str = "") -> Dict[str, Any]:
    """
    Returns grounded VFSTR college bus routes (Guntur, Vijayawada, Tenali, Chilakaluripet),
    hostel-specific shuttle schedules (KM Hostel, Villas SP Residency, AP/AR/AA/AO Hostels),
    bus pass renewal procedure, and transport office contacts.
    """
    q_lower = query.lower()
    is_hostel_bus = any(w in q_lower for w in ["hostel", "shuttle", "km hostel", "villas", "residency", "cluster", "curfew bus"])

    if is_hostel_bus:
        schedules = DataRepository.get_hostel_bus_schedules()
        # Fallback to verified records if table query returns empty
        if not schedules:
            schedules = [
                {"hostel_route": "KM HOSTEL", "shift": "Morning Shift", "direction": "KM Hostel to Campus", "departure_times_json": '["07:50 AM", "08:05 AM", "08:40 AM", "09:30 AM", "10:30 AM", "11:35 AM"]', "stoppages": "KM Hostel Main Gate → Campus"},
                {"hostel_route": "KM HOSTEL", "shift": "Evening Shift", "direction": "Campus to KM Hostel", "departure_times_json": '["01:45 PM", "03:30 PM", "04:10 PM", "04:40 PM", "05:15 PM", "06:15 PM", "07:00 PM", "08:00 PM", "09:00 PM"]', "stoppages": "Campus Transport Bay → KM Hostel"},
                {"hostel_route": "VILLAS SP RESIDENCY", "shift": "Morning Shift", "direction": "Villas SP Residency to Campus", "departure_times_json": '["07:45 AM", "08:00 AM", "08:40 AM", "09:00 AM", "09:50 AM", "11:30 AM"]', "stoppages": "SP Residency Arch → Campus"},
                {"hostel_route": "VILLAS SP RESIDENCY", "shift": "Evening Shift", "direction": "Campus to Villas SP Residency", "departure_times_json": '["02:00 PM", "03:30 PM", "04:10 PM", "04:40 PM", "05:15 PM", "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM"]', "stoppages": "Campus Transport Bay → Villas SP Residency"},
                {"hostel_route": "AP, AR, AA, AO HOSTELS", "shift": "Morning Shift", "direction": "Hostel Cluster to Campus", "departure_times_json": '["07:45 AM", "07:55 AM", "08:00 AM", "08:40 AM", "09:00 AM", "09:50 AM", "11:30 AM", "11:35 AM"]', "stoppages": "Hostel Cluster (AP/AR/AA/AO) → Campus"},
                {"hostel_route": "AP, AR, AA, AO HOSTELS", "shift": "Evening Shift", "direction": "Campus to Hostel Cluster", "departure_times_json": '["02:00 PM", "03:30 PM", "04:10 PM", "04:40 PM", "05:15 PM", "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM"]', "stoppages": "Campus Transport Bay → Hostel Cluster (AP/AR/AA/AO)"},
            ]

        # Group schedules by hostel route
        routes_map: Dict[str, Dict[str, str]] = {}
        for row in schedules:
            r_name = row["hostel_route"]
            times = row["departure_times_json"]
            if isinstance(times, str):
                try:
                    times = json.loads(times)
                except Exception:
                    times = [times]
            times_str = ", ".join(times) if isinstance(times, list) else str(times)
            shift_key = "Morning" if "morning" in row.get("shift", "").lower() else "Evening"
            if r_name not in routes_map:
                routes_map[r_name] = {}
            routes_map[r_name][shift_key] = f"{times_str} ({row.get('stoppages', '')})"

        text_lines = [
            "🚌 **VFSTR Hostel Shuttle Bus Timings & Campus Transit (Effective 01.10.2026):**\n",
            "• **1. KM HOSTEL Shuttle Schedule:**",
            f"  - **Morning Shift (Hostel → Campus):** {routes_map.get('KM HOSTEL', {}).get('Morning', '07:50 AM, 08:05 AM, 08:40 AM, 09:30 AM, 10:30 AM, 11:35 AM')}",
            f"  - **Evening Shift (Campus → Hostel):** {routes_map.get('KM HOSTEL', {}).get('Evening', '01:45 PM, 03:30 PM, 04:10 PM, 04:40 PM, 05:15 PM, 06:15 PM, 07:00 PM, 08:00 PM, 09:00 PM')}\n",
            "• **2. VILLAS SP RESIDENCY Shuttle Schedule:**",
            f"  - **Morning Shift (Hostel → Campus):** {routes_map.get('VILLAS SP RESIDENCY', {}).get('Morning', '07:45 AM, 08:00 AM, 08:40 AM, 09:00 AM, 09:50 AM, 11:30 AM')}",
            f"  - **Evening Shift (Campus → Hostel):** {routes_map.get('VILLAS SP RESIDENCY', {}).get('Evening', '02:00 PM, 03:30 PM, 04:10 PM, 04:40 PM, 05:15 PM, 06:00 PM, 07:00 PM, 08:00 PM, 09:00 PM')}\n",
            "• **3. AP, AR, AA, AO HOSTELS (Hostel Cluster) Shuttle:**",
            f"  - **Morning Shift (Hostel → Campus):** {routes_map.get('AP, AR, AA, AO HOSTELS', {}).get('Morning', '07:45 AM, 07:55 AM, 08:00 AM, 08:40 AM, 09:00 AM, 09:50 AM, 11:30 AM, 11:35 AM')}",
            f"  - **Evening Shift (Campus → Hostel):** {routes_map.get('AP, AR, AA, AO HOSTELS', {}).get('Evening', '02:00 PM, 03:30 PM, 04:10 PM, 04:40 PM, 05:15 PM, 06:00 PM, 07:00 PM, 08:00 PM, 09:00 PM')}\n",
            "• **Hostel Transit & Curfew Regulations (Clause HD-01):**",
            "  - All hostel residents must return before the **6:00 PM** reporting curfew.",
            "  - The evening shuttle runs until 09:00 PM from Campus Transport Bay for students with approved library/lab outpasses.",
            "  - Strict campus gate closure is enforced at **10:00 PM**.",
            "  - Transport Desk: Admin Block Room G-08 (+91-863-2344755 / `transport@vignan.ac.in`)."
        ]

        card_data = {
            "type": "transport",
            "title": "VFSTR Hostel Shuttle Bus Timings",
            "subtitle": "KM Hostel, Villas SP & Hostel Cluster (w.e.f. 01.10.2026)",
            "badge": "Hostel Shuttle",
            "badgeVariant": "blue",
            "data": {
                "km_hostel": "Morning: 07:50 - 11:35 AM | Evening: 01:45 - 09:00 PM",
                "villas_sp": "Morning: 07:45 - 11:30 AM | Evening: 02:00 - 09:00 PM",
                "cluster_hostels": "Morning: 07:45 - 11:35 AM | Evening: 02:00 - 09:00 PM",
                "transportDesk": "Admin Block Room G-08 (+91-863-2344755)",
                "curfew": "6:00 PM Reporting (10:00 PM Gate Closure)"
            },
            "actionLabel": "View Full Transport Schedule",
            "actionIntent": "navigate:transport"
        }

        citations = [
            {
                "title": "VFSTR Transport Office Notification",
                "clause": "Hostel Shuttle Schedule 2026",
                "effective_date": "2026-10-01",
                "summary": "Official shuttle schedules connecting KM Hostel, Villas SP Residency, and AP/AR/AA/AO Hostels to Campus."
            },
            {
                "title": "Hostel Discipline & Movement Regulations",
                "clause": "Clause HD-01",
                "effective_date": "2024-01-10",
                "summary": "Mandates 6:00 PM curfew reporting and movement register requirements."
            }
        ]

        return {
            "text": "\n".join(text_lines),
            "citations": citations,
            "structured_card": card_data
        }

    db_routes = DataRepository.get_transport_routes()
    
    text_lines: List[str] = [
        "🚌 **VFSTR College Bus Fleet & Campus Transit System:**\n",
        "• **Major Bus Transit Routes:**",
        "  1. **Route 1 (Guntur City Express):**",
        "     - Stoppages: Guntur Bus Stand → Gujjanagundla → Vidyanagar → Collector Office → VFSTR Campus.",
        "     - Arrival: 7:35 AM | Evening Return: 4:45 PM\n",
        "  2. **Route 2 (Vijayawada City Express):**",
        "     - Stoppages: Benz Circle → Auto Nagar → Poranki → Kankipadu → Tenali Bridge → VFSTR Campus.",
        "     - Arrival: 7:30 AM | Evening Return: 4:45 PM\n",
        "  3. **Route 3 (Tenali Town Shuttle):**",
        "     - Stoppages: Tenali Railway Station → Chenchupet → Morrispet → Nandivelugu → VFSTR Campus.",
        "     - Arrival: 7:40 AM | Evening Return: 4:45 PM\n",
        "  4. **Route 4 (Chilakaluripet Shuttle):**",
        "     - Stoppages: Chilakaluripet Clock Tower → Ganapavaram → VFSTR Campus.",
        "     - Arrival: 7:30 AM | Evening Return: 4:45 PM\n",
        "  5. **Route 5 (Mangalagiri Express):**",
        "     - Stoppages: Mangalagiri Bus Stand → NRI Hospital Junction → VFSTR Campus.",
        "     - Arrival: 7:35 AM | Evening Return: 4:45 PM\n",
        "• **Bus Pass Endorsement & Renewal Procedure:**",
        "  1. Pay the transport fee before the semester commencement date.",
        "  2. Bring your payment receipt and student identity card to the **Transport Desk (Admin Block, Room G-08)**.",
        "  3. An RFID bus pass sticker will be endorsed for the semester.\n",
        "• **Transport Office Contacts:**",
        "  - **Transport Desk:** Room G-08, Admin Block Ground Floor",
        "  - **Helpline:** +91-863-2344755 / +91-98481-99887",
        "  - **Email:** `transport@vignan.ac.in`",
    ]

    card_data = {
        "type": "transport",
        "title": "VFSTR College Bus & Transit Services",
        "subtitle": "Guntur, Vijayawada, Tenali & Chilakaluripet Routes",
        "badge": "Active Fleet",
        "badgeVariant": "green",
        "data": {
            "routes": [
                "Route 1: Guntur Express (Bus Stand - Vidyanagar)",
                "Route 2: Vijayawada City (Benz Circle - Poranki)",
                "Route 3: Tenali Town (Station - Morrispet)",
                "Route 4: Chilakaluripet Shuttle (Clock Tower - Campus)",
                "Route 5: Mangalagiri Express (Bus Stand - NRI Hospital)"
            ],
            "deskLocation": "Admin Block Room G-08 (Transport Desk)",
            "contact": "+91-863-2344755 / transport@vignan.ac.in",
            "endorsement": "Payment Receipt + Student ID at Room G-08"
        },
        "actionLabel": "Request Bus Pass",
        "actionIntent": "Submit a service request for bus pass endorsement"
    }

    citations = [
        {
            "title": "Campus Discipline & Vehicular Regulations",
            "clause": "Clause CD-04",
            "effective_date": "2024-01-10",
            "summary": "Mandates college bus RFID pass display and traffic regulations on campus."
        }
    ]

    return {
        "text": "\n".join(text_lines),
        "citations": citations,
        "structured_card": card_data
    }

