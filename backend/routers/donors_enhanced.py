"""
Enhanced Donor Management APIs
- Donor Deactivation/Reactivation
- Donation Sessions (Screening to Collection tracking)
- Rewards & Leaderboard
- Age calculation utilities
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime, timezone, date
import os
import uuid
import base64

from database import db
from models import (
    DonorReward, DonationSession, DEACTIVATION_REASONS, REWARD_TIERS, POINTS_CONFIG
)
from services import get_current_user

router = APIRouter(tags=["Donor Enhanced"])

# File upload directory for deactivation proofs
DEACTIVATION_PROOF_DIR = "/app/uploads/deactivation_proofs"
os.makedirs(DEACTIVATION_PROOF_DIR, exist_ok=True)

# Age limits (hardcoded as per requirement)
MIN_DONOR_AGE = 18
MAX_DONOR_AGE = 65


# ==================== UTILITY FUNCTIONS ====================

def calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD)"""
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return 0


def get_tier_from_donations(total_donations: int) -> str:
    """Determine tier based on total donations"""
    if total_donations >= 31:
        return "platinum"
    elif total_donations >= 16:
        return "gold"
    elif total_donations >= 6:
        return "silver"
    else:
        return "bronze"


def get_tier_progress(total_donations: int, current_tier: str) -> dict:
    """Get progress towards next tier"""
    tier_thresholds = {"bronze": 6, "silver": 16, "gold": 31, "platinum": float('inf')}
    next_tier_threshold = tier_thresholds.get(current_tier, float('inf'))
    
    if next_tier_threshold == float('inf'):
        return {"current": total_donations, "target": total_donations, "progress": 100, "next_tier": None}
    
    tier_names = ["bronze", "silver", "gold", "platinum"]
    current_idx = tier_names.index(current_tier) if current_tier in tier_names else 0
    next_tier = tier_names[current_idx + 1] if current_idx < len(tier_names) - 1 else None
    
    prev_threshold = [1, 6, 16, 31][current_idx]
    progress = ((total_donations - prev_threshold + 1) / (next_tier_threshold - prev_threshold + 1)) * 100
    
    return {
        "current": total_donations,
        "target": next_tier_threshold,
        "progress": min(progress, 100),
        "next_tier": next_tier
    }


async def generate_session_id() -> str:
    """Generate unique session ID"""
    count = await db.donation_sessions.count_documents({})
    return f"SES-{datetime.now().year}-{str(count + 1).zfill(5)}"


# ==================== DONOR DEACTIVATION ====================

@router.post("/donors/{donor_id}/deactivate")
async def deactivate_donor(
    donor_id: str,
    reason: str = Form(...),
    notes: Optional[str] = Form(None),
    proof_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a donor with reason and optional proof"""
    if reason not in DEACTIVATION_REASONS:
        raise HTTPException(status_code=400, detail=f"Invalid reason. Must be one of: {DEACTIVATION_REASONS}")
    
    donor = await db.donors.find_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    if not donor.get("is_active", True):
        raise HTTPException(status_code=400, detail="Donor is already deactivated")
    
    # Handle proof file upload
    proof_url = None
    if proof_file:
        # Validate file
        allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
        file_ext = os.path.splitext(proof_file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File extension must be one of: {allowed_extensions}")
        
        contents = await proof_file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Save file
        unique_id = str(uuid.uuid4())[:8]
        filename = f"deactivation_{donor_id}_{unique_id}{file_ext}"
        filepath = os.path.join(DEACTIVATION_PROOF_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(contents)
        
        proof_url = f"/uploads/deactivation_proofs/{filename}"
    
    # Update donor
    update_data = {
        "is_active": False,
        "deactivation_reason": reason,
        "deactivation_notes": notes,
        "deactivation_proof_url": proof_url,
        "deactivated_by": current_user["id"],
        "deactivated_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user["id"]
    }
    
    await db.donors.update_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"$set": update_data}
    )
    
    return {"status": "success", "message": "Donor deactivated successfully"}


@router.post("/donors/{donor_id}/reactivate")
async def reactivate_donor(
    donor_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Reactivate a deactivated donor (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reactivate donors")
    
    donor = await db.donors.find_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    if donor.get("is_active", True):
        raise HTTPException(status_code=400, detail="Donor is already active")
    
    # Add to reactivation history
    reactivation_entry = {
        "reactivated_at": datetime.now(timezone.utc).isoformat(),
        "reactivated_by": current_user["id"],
        "reason": reason,
        "previous_deactivation_reason": donor.get("deactivation_reason"),
        "previous_deactivation_date": donor.get("deactivated_at")
    }
    
    reactivation_history = donor.get("reactivation_history", [])
    reactivation_history.append(reactivation_entry)
    
    # Update donor
    update_data = {
        "is_active": True,
        "deactivation_reason": None,
        "deactivation_notes": None,
        "deactivation_proof_url": None,
        "deactivated_by": None,
        "deactivated_at": None,
        "reactivation_history": reactivation_history,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user["id"]
    }
    
    await db.donors.update_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"$set": update_data}
    )
    
    return {"status": "success", "message": "Donor reactivated successfully"}


# ==================== DONOR ELIGIBILITY WITH STATUS ====================

@router.get("/donors-with-status")
async def get_donors_with_eligibility_status(
    filter_status: Optional[str] = None,  # all, eligible, not_eligible
    blood_group: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[str] = None,  # active, deactivated, all
    current_user: dict = Depends(get_current_user)
):
    """Get all donors with their eligibility status for collection"""
    query = {}
    
    # Active filter
    if is_active == "active":
        query["is_active"] = {"$ne": False}
    elif is_active == "deactivated":
        query["is_active"] = False
    # "all" - no filter
    
    if blood_group:
        query["blood_group"] = blood_group
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"donor_id": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    
    donors = await db.donors.find(query, {"_id": 0, "qr_code": 0}).to_list(1000)
    
    result = []
    today = date.today()
    
    for donor in donors:
        age = calculate_age(donor.get("date_of_birth", ""))
        
        # Determine eligibility status
        eligibility_status = "eligible"
        eligibility_reason = None
        eligible_date = None
        
        # Check if deactivated
        if not donor.get("is_active", True):
            eligibility_status = "deactivated"
            eligibility_reason = donor.get("deactivation_reason", "Deactivated")
        
        # Check age
        elif age < MIN_DONOR_AGE or age > MAX_DONOR_AGE:
            eligibility_status = "age_restriction"
            eligibility_reason = f"Age must be between {MIN_DONOR_AGE} and {MAX_DONOR_AGE} years"
        
        # Check deferral
        elif donor.get("status") == "deferred_permanent":
            eligibility_status = "deferred"
            eligibility_reason = donor.get("deferral_reason", "Permanently deferred")
        
        elif donor.get("status") == "deferred_temporary":
            deferral_end = donor.get("deferral_end_date")
            if deferral_end:
                end_date = datetime.fromisoformat(deferral_end).date()
                if end_date > today:
                    eligibility_status = "deferred"
                    eligibility_reason = donor.get("deferral_reason", "Temporarily deferred")
                    eligible_date = deferral_end
        
        # Check last donation interval
        elif donor.get("last_donation_date"):
            last_donation = datetime.fromisoformat(donor["last_donation_date"]).date()
            days_since = (today - last_donation).days
            if days_since < 56:
                eligibility_status = "not_eligible"
                eligible_date = (last_donation + timedelta(days=56)).isoformat()
                eligibility_reason = f"Must wait {56 - days_since} more days (minimum 56 days between donations)"
        
        # Check for active donation session
        active_session = await db.donation_sessions.find_one({
            "donor_id": donor["id"],
            "current_stage": {"$in": ["screening", "collection"]}
        })
        if active_session:
            eligibility_status = "in_progress"
            eligibility_reason = f"Active session: {active_session.get('current_stage')}"
        
        donor_with_status = {
            **donor,
            "age": age,
            "eligibility_status": eligibility_status,
            "eligibility_reason": eligibility_reason,
            "eligible_date": eligible_date
        }
        
        # Apply filter
        if filter_status == "eligible" and eligibility_status != "eligible":
            continue
        elif filter_status == "not_eligible" and eligibility_status == "eligible":
            continue
        
        result.append(donor_with_status)
    
    # Sort by oldest last donation first (eligible donors prioritized)
    result.sort(key=lambda x: (
        0 if x["eligibility_status"] == "eligible" else 1,
        x.get("last_donation_date") or "9999-12-31"
    ))
    
    return result


# ==================== DONATION SESSIONS ====================

@router.post("/donation-sessions")
async def create_donation_session(
    donor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new donation session (Start Screening)"""
    donor = await db.donors.find_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    # Check eligibility
    age = calculate_age(donor.get("date_of_birth", ""))
    
    if not donor.get("is_active", True):
        raise HTTPException(status_code=400, detail="Donor is deactivated")
    
    if age < MIN_DONOR_AGE or age > MAX_DONOR_AGE:
        raise HTTPException(status_code=400, detail=f"Donor age ({age}) must be between {MIN_DONOR_AGE} and {MAX_DONOR_AGE}")
    
    if donor.get("status") == "deferred_permanent":
        raise HTTPException(status_code=400, detail="Donor is permanently deferred")
    
    if donor.get("status") == "deferred_temporary":
        deferral_end = donor.get("deferral_end_date")
        if deferral_end:
            end_date = datetime.fromisoformat(deferral_end).date()
            if end_date > date.today():
                raise HTTPException(status_code=400, detail=f"Donor is deferred until {deferral_end}")
    
    if donor.get("last_donation_date"):
        last_donation = datetime.fromisoformat(donor["last_donation_date"]).date()
        days_since = (date.today() - last_donation).days
        if days_since < 56:
            raise HTTPException(status_code=400, detail=f"Only {days_since} days since last donation. Minimum 56 days required.")
    
    # Check for existing active session
    existing_session = await db.donation_sessions.find_one({
        "donor_id": donor["id"],
        "current_stage": {"$in": ["screening", "collection"]}
    })
    if existing_session:
        raise HTTPException(status_code=400, detail=f"Donor has an active session (Stage: {existing_session['current_stage']})")
    
    # Create session
    session = DonationSession(
        session_id=await generate_session_id(),
        donor_id=donor["id"],
        screening_started_at=datetime.now(timezone.utc).isoformat(),
        current_stage="screening",
        started_by=current_user["id"]
    )
    
    doc = session.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.donation_sessions.insert_one(doc)
    
    return {
        "status": "success",
        "session_id": session.session_id,
        "id": session.id,
        "donor_id": donor["id"],
        "donor_code": donor["donor_id"],
        "current_stage": session.current_stage
    }


@router.get("/donation-sessions")
async def get_donation_sessions(
    status: Optional[str] = None,  # active, completed, rejected, cancelled
    donor_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get donation sessions"""
    query = {}
    
    if status == "active":
        query["current_stage"] = {"$in": ["screening", "collection"]}
    elif status:
        query["current_stage"] = status
    
    if donor_id:
        donor = await db.donors.find_one(
            {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
            {"_id": 0, "id": 1}
        )
        if donor:
            query["donor_id"] = donor["id"]
    
    sessions = await db.donation_sessions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with donor info
    for session in sessions:
        donor = await db.donors.find_one({"id": session["donor_id"]}, {"_id": 0, "full_name": 1, "donor_id": 1, "blood_group": 1})
        if donor:
            session["donor_name"] = donor.get("full_name")
            session["donor_code"] = donor.get("donor_id")
            session["blood_group"] = donor.get("blood_group")
    
    return sessions


@router.get("/donation-sessions/{session_id}")
async def get_donation_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific donation session"""
    session = await db.donation_sessions.find_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Enrich with donor info
    donor = await db.donors.find_one({"id": session["donor_id"]}, {"_id": 0})
    if donor:
        session["donor"] = donor
    
    return session


@router.put("/donation-sessions/{session_id}/complete-screening")
async def complete_session_screening(
    session_id: str,
    screening_id: str,
    status: str,  # eligible, rejected
    rejection_reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Complete screening phase of donation session"""
    session = await db.donation_sessions.find_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["current_stage"] != "screening":
        raise HTTPException(status_code=400, detail="Session is not in screening stage")
    
    update_data = {
        "screening_id": screening_id,
        "screening_completed_at": datetime.now(timezone.utc).isoformat(),
        "screening_status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status == "eligible":
        update_data["current_stage"] = "collection"
    else:
        update_data["current_stage"] = "rejected"
        update_data["rejection_reason"] = rejection_reason
    
    await db.donation_sessions.update_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"$set": update_data}
    )
    
    return {"status": "success", "current_stage": update_data["current_stage"]}


@router.put("/donation-sessions/{session_id}/complete-collection")
async def complete_session_collection(
    session_id: str,
    donation_id: str,
    unit_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete collection phase of donation session"""
    session = await db.donation_sessions.find_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["current_stage"] != "collection":
        raise HTTPException(status_code=400, detail="Session is not in collection stage")
    
    update_data = {
        "donation_id": donation_id,
        "unit_id": unit_id,
        "collection_completed_at": datetime.now(timezone.utc).isoformat(),
        "current_stage": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.donation_sessions.update_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"$set": update_data}
    )
    
    # Update donor rewards
    await update_donor_rewards(session["donor_id"], "whole_blood")
    
    return {"status": "success", "current_stage": "completed"}


@router.put("/donation-sessions/{session_id}/cancel")
async def cancel_donation_session(
    session_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an active donation session"""
    session = await db.donation_sessions.find_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["current_stage"] not in ["screening", "collection"]:
        raise HTTPException(status_code=400, detail="Can only cancel active sessions")
    
    update_data = {
        "current_stage": "cancelled",
        "cancelled_reason": reason,
        "cancelled_by": current_user["id"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.donation_sessions.update_one(
        {"$or": [{"id": session_id}, {"session_id": session_id}]},
        {"$set": update_data}
    )
    
    return {"status": "success", "message": "Session cancelled"}


# ==================== REWARDS & LEADERBOARD ====================

async def update_donor_rewards(donor_id: str, donation_type: str = "whole_blood", is_emergency: bool = False):
    """Update donor rewards after a donation"""
    donor = await db.donors.find_one({"id": donor_id}, {"_id": 0})
    if not donor:
        return
    
    # Get or create rewards record
    rewards = await db.donor_rewards.find_one({"donor_id": donor_id}, {"_id": 0})
    
    if not rewards:
        rewards = DonorReward(donor_id=donor_id)
        rewards_doc = rewards.model_dump()
        rewards_doc['created_at'] = rewards_doc['created_at'].isoformat()
        rewards_doc['updated_at'] = rewards_doc['updated_at'].isoformat()
        await db.donor_rewards.insert_one(rewards_doc)
        rewards = rewards_doc
    
    # Calculate points
    points = POINTS_CONFIG.get(donation_type, 10)
    if is_emergency:
        points += POINTS_CONFIG["emergency_bonus"]
    
    total_donations = rewards.get("total_donations", 0) + 1
    total_points = rewards.get("points_earned", 0) + points
    
    # Check for milestone badges
    badges = rewards.get("badges", [])
    new_badges = []
    
    milestone_badges = {
        1: "first_donation",
        5: "donation_5",
        10: "donation_10",
        25: "donation_25",
        50: "donation_50"
    }
    
    if total_donations in milestone_badges:
        badge_name = milestone_badges[total_donations]
        if not any(b.get("badge") == badge_name for b in badges):
            new_badge = {
                "badge": badge_name,
                "earned_at": datetime.now(timezone.utc).isoformat()
            }
            badges.append(new_badge)
            new_badges.append(badge_name)
            
            # Add milestone points
            milestone_points = POINTS_CONFIG.get(f"milestone_{total_donations}", 0)
            total_points += milestone_points
    
    # Check for rare blood type badge
    rare_types = ["AB-", "B-", "O-"]
    if donor.get("blood_group") in rare_types:
        if not any(b.get("badge") == "rare_blood_type" for b in badges):
            badges.append({
                "badge": "rare_blood_type",
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
            new_badges.append("rare_blood_type")
    
    # Emergency badge
    if is_emergency and not any(b.get("badge") == "emergency_donor" for b in badges):
        badges.append({
            "badge": "emergency_donor",
            "earned_at": datetime.now(timezone.utc).isoformat()
        })
        new_badges.append("emergency_donor")
    
    # Determine tier
    tier = get_tier_from_donations(total_donations)
    
    # Update rewards
    await db.donor_rewards.update_one(
        {"donor_id": donor_id},
        {
            "$set": {
                "points_earned": total_points,
                "total_donations": total_donations,
                "tier": tier,
                "badges": badges,
                "last_donation_points": points,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"new_badges": new_badges, "points_earned": points, "total_points": total_points, "tier": tier}


@router.get("/donor-rewards/{donor_id}")
async def get_donor_rewards(donor_id: str, current_user: dict = Depends(get_current_user)):
    """Get rewards for a specific donor"""
    donor = await db.donors.find_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    rewards = await db.donor_rewards.find_one({"donor_id": donor["id"]}, {"_id": 0})
    
    if not rewards:
        rewards = {
            "donor_id": donor["id"],
            "points_earned": 0,
            "total_donations": donor.get("total_donations", 0),
            "tier": get_tier_from_donations(donor.get("total_donations", 0)),
            "badges": []
        }
    
    # Add tier progress
    rewards["tier_progress"] = get_tier_progress(rewards.get("total_donations", 0), rewards.get("tier", "bronze"))
    
    return rewards


@router.get("/leaderboard")
async def get_leaderboard(
    period: str = "all_time",  # all_time, year, month
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get donor leaderboard"""
    # For now, use total_donations as the ranking criteria
    # In production, you might want to filter by donation dates for year/month
    
    rewards = await db.donor_rewards.find({}, {"_id": 0}).sort("points_earned", -1).to_list(limit)
    
    leaderboard = []
    rank = 1
    
    for reward in rewards:
        donor = await db.donors.find_one({"id": reward["donor_id"]}, {"_id": 0, "full_name": 1, "donor_id": 1, "blood_group": 1})
        if donor:
            leaderboard.append({
                "rank": rank,
                "donor_id": donor.get("donor_id"),
                "full_name": donor.get("full_name"),
                "blood_group": donor.get("blood_group"),
                "total_donations": reward.get("total_donations", 0),
                "points_earned": reward.get("points_earned", 0),
                "tier": reward.get("tier", "bronze"),
                "badges_count": len(reward.get("badges", []))
            })
            rank += 1
    
    return {
        "period": period,
        "leaderboard": leaderboard,
        "total_donors": len(leaderboard)
    }


# ==================== SCREENING LIST (ELIGIBLE DONORS) ====================

@router.get("/screening/eligible-donors")
async def get_eligible_donors_for_screening(
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all eligible donors for screening (active, not deferred, meets age/interval requirements)"""
    query = {
        "is_active": {"$ne": False}
    }
    
    if blood_group:
        query["blood_group"] = blood_group
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"donor_id": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    
    donors = await db.donors.find(query, {"_id": 0, "qr_code": 0}).to_list(1000)
    
    eligible_donors = []
    today = date.today()
    
    for donor in donors:
        age = calculate_age(donor.get("date_of_birth", ""))
        
        # Check age limits
        if age < MIN_DONOR_AGE or age > MAX_DONOR_AGE:
            continue
        
        # Check permanent deferral
        if donor.get("status") == "deferred_permanent":
            continue
        
        # Check temporary deferral
        if donor.get("status") == "deferred_temporary":
            deferral_end = donor.get("deferral_end_date")
            if deferral_end:
                end_date = datetime.fromisoformat(deferral_end).date()
                if end_date > today:
                    continue
        
        # Check donation interval (56 days)
        if donor.get("last_donation_date"):
            last_donation = datetime.fromisoformat(donor["last_donation_date"]).date()
            days_since = (today - last_donation).days
            if days_since < 56:
                continue
        
        # Check for active session
        active_session = await db.donation_sessions.find_one({
            "donor_id": donor["id"],
            "current_stage": {"$in": ["screening", "collection"]}
        })
        if active_session:
            continue
        
        donor["age"] = age
        eligible_donors.append(donor)
    
    # Sort by oldest last donation first
    eligible_donors.sort(key=lambda x: x.get("last_donation_date") or "0000-00-00")
    
    return eligible_donors


# ==================== DONOR DETAIL ENRICHMENT ====================

@router.get("/donors/{donor_id}/full-profile")
async def get_donor_full_profile(donor_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete donor profile with age, eligibility, rewards, and history"""
    donor = await db.donors.find_one(
        {"$or": [{"id": donor_id}, {"donor_id": donor_id}]},
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    # Calculate age
    age = calculate_age(donor.get("date_of_birth", ""))
    donor["age"] = age
    
    # Get eligibility status
    eligibility = await check_donor_full_eligibility(donor)
    
    # Get rewards
    rewards = await db.donor_rewards.find_one({"donor_id": donor["id"]}, {"_id": 0})
    if not rewards:
        rewards = {
            "points_earned": 0,
            "total_donations": donor.get("total_donations", 0),
            "tier": get_tier_from_donations(donor.get("total_donations", 0)),
            "badges": []
        }
    rewards["tier_progress"] = get_tier_progress(rewards.get("total_donations", 0), rewards.get("tier", "bronze"))
    
    # Get active session if any
    active_session = await db.donation_sessions.find_one({
        "donor_id": donor["id"],
        "current_stage": {"$in": ["screening", "collection"]}
    }, {"_id": 0})
    
    # Get recent donations
    donations = await db.donations.find({"donor_id": donor["id"]}, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    # Get recent screenings
    screenings = await db.screenings.find({"donor_id": donor["id"]}, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    return {
        "donor": donor,
        "eligibility": eligibility,
        "rewards": rewards,
        "active_session": active_session,
        "recent_donations": donations,
        "recent_screenings": screenings
    }


async def check_donor_full_eligibility(donor: dict) -> dict:
    """Check complete eligibility status for a donor"""
    age = calculate_age(donor.get("date_of_birth", ""))
    today = date.today()
    
    status = "eligible"
    reasons = []
    can_start_screening = True
    can_start_collection = False
    eligible_date = None
    
    # Check if deactivated
    if not donor.get("is_active", True):
        status = "deactivated"
        reasons.append(f"Deactivated: {donor.get('deactivation_reason', 'Unknown reason')}")
        can_start_screening = False
    
    # Check age
    elif age < MIN_DONOR_AGE:
        status = "age_restriction"
        reasons.append(f"Below minimum age ({MIN_DONOR_AGE} years)")
        can_start_screening = False
    elif age > MAX_DONOR_AGE:
        status = "age_restriction"
        reasons.append(f"Above maximum age ({MAX_DONOR_AGE} years)")
        can_start_screening = False
    
    # Check deferral
    elif donor.get("status") == "deferred_permanent":
        status = "deferred"
        reasons.append(f"Permanently deferred: {donor.get('deferral_reason', 'Medical reason')}")
        can_start_screening = False
    
    elif donor.get("status") == "deferred_temporary":
        deferral_end = donor.get("deferral_end_date")
        if deferral_end:
            end_date = datetime.fromisoformat(deferral_end).date()
            if end_date > today:
                status = "deferred"
                reasons.append(f"Deferred until {deferral_end}: {donor.get('deferral_reason', 'Temporary deferral')}")
                eligible_date = deferral_end
                can_start_screening = False
    
    # Check donation interval
    if can_start_screening and donor.get("last_donation_date"):
        last_donation = datetime.fromisoformat(donor["last_donation_date"]).date()
        days_since = (today - last_donation).days
        if days_since < 56:
            status = "not_eligible"
            next_eligible = last_donation + timedelta(days=56)
            reasons.append(f"Only {days_since} days since last donation. Eligible again on {next_eligible.isoformat()}")
            eligible_date = next_eligible.isoformat()
            can_start_screening = False
    
    # Check for active session
    active_session = await db.donation_sessions.find_one({
        "donor_id": donor["id"],
        "current_stage": {"$in": ["screening", "collection"]}
    })
    if active_session:
        status = "in_progress"
        reasons.append(f"Active session in {active_session['current_stage']} stage")
        can_start_screening = False
        if active_session["current_stage"] == "collection":
            can_start_collection = True
    
    return {
        "status": status,
        "reasons": reasons,
        "can_start_screening": can_start_screening,
        "can_start_collection": can_start_collection,
        "eligible_date": eligible_date,
        "age": age,
        "active_session_id": active_session.get("session_id") if active_session else None
    }


# Import timedelta for date calculations
from datetime import timedelta
