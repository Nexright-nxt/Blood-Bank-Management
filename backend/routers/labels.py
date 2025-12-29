from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from services import get_current_user

router = APIRouter(prefix="/labels", tags=["Labels"])

# Storage temperature requirements
STORAGE_TEMPS = {
    "whole_blood": "2-6°C",
    "prc": "2-6°C",
    "plasma": "≤ -25°C",
    "ffp": "≤ -25°C",
    "platelets": "20-24°C",
    "cryoprecipitate": "≤ -25°C",
}

@router.get("/blood-unit/{unit_id}")
async def get_blood_unit_label_data(
    unit_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get label data for a blood unit"""
    # Try to find by unit_id field first, then by id
    unit = await db.blood_units.find_one(
        {"$or": [{"unit_id": unit_id}, {"id": unit_id}]},
        {"_id": 0}
    )
    
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    
    # Get donation info for donor reference
    donation = None
    if unit.get("donation_id"):
        donation = await db.donations.find_one(
            {"id": unit["donation_id"]},
            {"_id": 0}
        )
    
    # Get lab test results
    lab_test = await db.lab_tests.find_one(
        {"unit_id": unit.get("id")},
        {"_id": 0}
    )
    
    # Determine test status
    test_status = "pending"
    if lab_test:
        if lab_test.get("overall_result") == "negative":
            test_status = "negative"
        elif lab_test.get("overall_result") == "positive":
            test_status = "positive"
        else:
            test_status = "tested"
    
    # Build warnings list
    warnings = []
    if lab_test and lab_test.get("overall_result") == "positive":
        warnings.append("REACTIVE - DO NOT USE")
    if unit.get("status") == "quarantine":
        warnings.append("QUARANTINED")
    
    # Check expiry
    if unit.get("expiry_date"):
        try:
            expiry = datetime.fromisoformat(unit["expiry_date"].replace("Z", "+00:00"))
            if expiry.date() <= datetime.now(timezone.utc).date():
                warnings.append("EXPIRED")
        except:
            pass
    
    label_data = {
        "unit_id": unit.get("unit_id") or unit.get("id"),
        "blood_group": unit.get("confirmed_blood_group") or unit.get("blood_group"),
        "component_type": "whole_blood",
        "volume": unit.get("volume", 450),
        "collection_date": unit.get("collection_date"),
        "expiry_date": unit.get("expiry_date"),
        "donor_id": unit.get("donor_id", "")[-8:] if unit.get("donor_id") else "Anonymous",
        "test_status": test_status,
        "batch_number": unit.get("batch_id") or unit.get("lot_number"),
        "storage_location": unit.get("storage_location") or unit.get("current_location"),
        "storage_temp": STORAGE_TEMPS.get("whole_blood", "2-6°C"),
        "blood_bank_name": "BLOODLINK BLOOD BANK",
        "warnings": warnings,
        "status": unit.get("status"),
    }
    
    return label_data


@router.get("/component/{component_id}")
async def get_component_label_data(
    component_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get label data for a blood component"""
    # Try to find by component_id field first, then by id
    component = await db.components.find_one(
        {"$or": [{"component_id": component_id}, {"id": component_id}]},
        {"_id": 0}
    )
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Get parent unit info
    parent_unit = None
    if component.get("parent_unit_id"):
        parent_unit = await db.blood_units.find_one(
            {"id": component["parent_unit_id"]},
            {"_id": 0}
        )
    
    # Get lab test from parent unit
    test_status = "tested"  # Components are usually from tested units
    if parent_unit:
        lab_test = await db.lab_tests.find_one(
            {"unit_id": parent_unit.get("id")},
            {"_id": 0}
        )
        if lab_test:
            if lab_test.get("overall_result") == "negative":
                test_status = "negative"
            elif lab_test.get("overall_result") == "positive":
                test_status = "positive"
    
    # Build warnings
    warnings = []
    if component.get("status") == "quarantine":
        warnings.append("QUARANTINED")
    
    # Check expiry
    if component.get("expiry_date"):
        try:
            expiry = datetime.fromisoformat(component["expiry_date"].replace("Z", "+00:00"))
            if expiry.date() <= datetime.now(timezone.utc).date():
                warnings.append("EXPIRED")
        except:
            pass
    
    component_type = component.get("component_type", "prc")
    
    label_data = {
        "unit_id": component.get("component_id") or component.get("id"),
        "blood_group": component.get("blood_group") or (parent_unit.get("confirmed_blood_group") if parent_unit else None),
        "component_type": component_type,
        "volume": component.get("volume", 200),
        "collection_date": component.get("processing_date") or component.get("created_at", "")[:10],
        "expiry_date": component.get("expiry_date"),
        "donor_id": (parent_unit.get("donor_id", "")[-8:] if parent_unit and parent_unit.get("donor_id") else "Anonymous"),
        "test_status": test_status,
        "batch_number": component.get("batch_id") or component.get("lot_number"),
        "storage_location": component.get("storage_location"),
        "storage_temp": STORAGE_TEMPS.get(component_type, "2-6°C"),
        "blood_bank_name": "BLOODLINK BLOOD BANK",
        "warnings": warnings,
        "status": component.get("status"),
        "parent_unit_id": component.get("parent_unit_id"),
    }
    
    return label_data


@router.post("/bulk")
async def get_bulk_label_data(
    unit_ids: List[str] = [],
    component_ids: List[str] = [],
    current_user: dict = Depends(get_current_user)
):
    """Get label data for multiple units and/or components"""
    results = []
    
    # Fetch blood units
    for unit_id in unit_ids:
        try:
            unit_data = await get_blood_unit_label_data(unit_id, current_user)
            results.append(unit_data)
        except HTTPException:
            continue
    
    # Fetch components
    for comp_id in component_ids:
        try:
            comp_data = await get_component_label_data(comp_id, current_user)
            results.append(comp_data)
        except HTTPException:
            continue
    
    return results
