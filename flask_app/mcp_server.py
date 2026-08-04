#!/usr/bin/env python3
"""
MCP server for Fire Department Management System.

Exposes tools so an AI assistant (Claude Desktop, ChatGPT Desktop, etc.)
can read old paper inspection records from a photo and enter them into the
database — including backdated inspections.

Setup:
    pip install mcp
    Add to Claude Desktop config (see README section below).
"""
import sys
import os
import json
from datetime import datetime

# Make sure we can import db_helpers regardless of where this is launched from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db_helpers

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Fire Department Management",
    instructions=(
        "You help enter old paper vehicle inspection records into the fire department "
        "management system. When given an image of a paper inspection record: "
        "1. Call list_vehicles to find the right vehicle. "
        "2. Call list_firefighters to find the inspector by name. "
        "3. Call get_vehicle_checklist with the vehicle ID to see what items to check. "
        "4. Match items from the paper record to the checklist items. "
        "5. Call submit_inspection with the date from the paper record, the results, and any notes. "
        "Always confirm the vehicle and date with the user before submitting."
    )
)


@mcp.tool()
def list_vehicles() -> str:
    """List all active vehicles in the fleet with their IDs and codes."""
    vehicles = db_helpers.get_all_vehicles()
    result = []
    for v in vehicles:
        result.append({
            "id": v["id"],
            "code": v["vehicle_code"],
            "name": v["name"],
            "type": v.get("vehicle_type", ""),
        })
    return json.dumps(result, indent=2)


@mcp.tool()
def list_firefighters() -> str:
    """List all firefighters with their IDs and names."""
    firefighters = db_helpers.get_all_firefighters()
    result = []
    for f in firefighters:
        result.append({
            "id": f["id"],
            "number": f["fireman_number"],
            "name": f["full_name"],
        })
    return json.dumps(result, indent=2)


@mcp.tool()
def get_vehicle_checklist(vehicle_id: int) -> str:
    """
    Get the inspection checklist items assigned to a specific vehicle.

    Args:
        vehicle_id: The vehicle's database ID (from list_vehicles).
    """
    items = db_helpers.get_vehicle_checklist(vehicle_id)
    result = []
    for item in items:
        result.append({
            "id": item["id"],
            "description": item["description"],
            "category": item.get("category", ""),
        })
    return json.dumps(result, indent=2)


@mcp.tool()
def submit_inspection(
    vehicle_id: int,
    inspector_id: int,
    inspection_date: str,
    results: list,
    additional_notes: str = "",
) -> str:
    """
    Submit a vehicle inspection. Supports backdating for old paper records.

    Args:
        vehicle_id: The vehicle's database ID (from list_vehicles).
        inspector_id: The firefighter's database ID (from list_firefighters).
        inspection_date: Date of inspection in YYYY-MM-DD format (use the date
            from the paper record, even if it's months or years ago).
        results: List of checklist item results. Each item must have:
            - item_id (int): checklist item ID from get_vehicle_checklist
            - status (str): "pass" or "fail"
            - notes (str, optional): notes about a failure
        additional_notes: Any overall notes from the paper record.

    Returns:
        Confirmation message with the new inspection ID, or an error message.
    """
    # Validate date
    try:
        parsed = datetime.strptime(inspection_date, "%Y-%m-%d")
        iso_date = parsed.replace(hour=12, minute=0, second=0).isoformat()
    except ValueError:
        return f"Error: invalid date '{inspection_date}'. Use YYYY-MM-DD format."

    # Validate results format
    formatted_results = []
    for r in results:
        if "item_id" not in r or "status" not in r:
            return "Error: each result must have 'item_id' and 'status' fields."
        if r["status"] not in ("pass", "fail"):
            return f"Error: status must be 'pass' or 'fail', got '{r['status']}'."
        formatted_results.append({
            "item_id": int(r["item_id"]),
            "status": r["status"],
            "notes": r.get("notes", ""),
        })

    if not formatted_results:
        return "Error: no results provided."

    success, result = db_helpers.create_vehicle_inspection(
        vehicle_id=vehicle_id,
        inspector_id=inspector_id,
        inspection_results=formatted_results,
        additional_notes=additional_notes,
        inspection_date=iso_date,
    )

    if success:
        vehicle = db_helpers.get_vehicle_by_id(vehicle_id)
        vehicle_name = vehicle["name"] if vehicle else f"Vehicle {vehicle_id}"
        passed_count = sum(1 for r in formatted_results if r["status"] == "pass")
        failed_count = sum(1 for r in formatted_results if r["status"] == "fail")
        overall = "PASSED" if failed_count == 0 else "FAILED"
        return (
            f"Inspection submitted successfully.\n"
            f"  Inspection ID: {result}\n"
            f"  Vehicle: {vehicle_name}\n"
            f"  Date: {inspection_date}\n"
            f"  Result: {overall} ({passed_count} pass, {failed_count} fail)\n"
            f"  Items checked: {len(formatted_results)}"
        )
    else:
        return f"Error saving inspection: {result}"


@mcp.tool()
def get_recent_inspections(vehicle_id: int, limit: int = 5) -> str:
    """
    Get recent inspection history for a vehicle — useful for checking
    whether a paper record has already been entered.

    Args:
        vehicle_id: The vehicle's database ID.
        limit: How many recent inspections to return (default 5).
    """
    history = db_helpers.get_vehicle_inspection_history(vehicle_id, limit=limit)
    if not history:
        return json.dumps({"inspections": [], "message": "No inspection history found."})

    result = []
    for h in history:
        result.append({
            "id": h["id"],
            "date": h["inspection_date"],
            "inspector": h.get("full_name", "Unknown"),
            "passed": h["passed"],
            "notes": h.get("additional_notes", ""),
        })
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()
