"""RiderEx — FastAPI backend"""
import os
import json
import random
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from agents import run_riderex_pipeline
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="RiderEx")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Supabase client (optional — gracefully disabled if not configured) ──
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Supabase unavailable: {e}")
        return None

def _lookup_vehicle(vehicle_id: str) -> dict:
    """Return the registry entry for a vehicle_id, or {}."""
    try:
        with open("riderex_vehicles.json") as f:
            vlist = json.load(f).get("vehicles", [])
        return next((v for v in vlist if v.get("vehicle_id") == vehicle_id), {})
    except Exception:
        return {}

def save_to_supabase(result: dict, feedback_text: str = ""):
    sb = get_supabase()
    if not sb:
        return
    try:
        intake     = dict(result.get("intake", {}))
        safety     = result.get("safety", {})
        resolution = result.get("resolution", {})
        review     = result.get("quality_review", {})
        handoff    = result.get("engineering_handoff", {})

        # Embed raw feedback into intake_data so it travels with the record
        if feedback_text and not intake.get("raw_feedback"):
            intake["raw_feedback"] = feedback_text

        # Look up vehicle metadata from registry
        vehicle_id = result.get("vehicle_id", "")
        vinfo = _lookup_vehicle(vehicle_id)
        vehicle_type    = vinfo.get("model", "—")
        software_version = vinfo.get("software_version", "—")

        # Approved customer-facing response (review agent overrides resolution agent)
        customer_response = (
            review.get("final_customer_response")
            or resolution.get("customer_response", "")
        )

        sb.table("rides").insert({
            "ticket_id":            intake.get("ticket_id"),
            "ride_id":              result.get("ride_id"),
            "vehicle_id":           vehicle_id,
            "vehicle_type":         vehicle_type,
            "software_version":     software_version,
            "category":             intake.get("category"),
            "priority":             intake.get("priority"),
            "safety_level":         safety.get("safety_level"),
            "nhtsa":                bool(safety.get("nhtsa_reportable")),
            "rating":               result.get("rating"),
            "churn_risk":           intake.get("churn_risk"),
            "refund_amount":        resolution.get("refund_amount", 0),
            "credit_amount":        resolution.get("credit_amount", 0),
            "good_ride":            intake.get("category") == "COMPLIMENT" or (
                                        safety.get("safety_level") == "NONE" and
                                        intake.get("priority") == "P4"
                                    ),
            "sentiment":            intake.get("sentiment"),
            "quality_score":        review.get("quality_score"),
            "review_decision":      review.get("review_decision"),
            "requires_engineering": bool(handoff.get("requires_engineering")),
            "engineering_team":     handoff.get("engineering_team", "NONE"),
            "vehicle_action":       safety.get("recommended_vehicle_action", "NONE"),
            "action_items":         len(resolution.get("action_items", [])),
            "band_messages":        result.get("band_messages", 0),
            "key_phrases":          intake.get("key_phrases", []),
            "intake_data":          intake,          # includes raw_feedback
            "safety_data":          safety,
            "resolution_data":      resolution,      # includes customer_response
            "review_data":          review,          # includes final_customer_response
            "engineering_data":     handoff,
        }).execute()
        logger.info(f"[Supabase] Saved {intake.get('ticket_id')} | {vehicle_id} | {vehicle_type} | feedback={'yes' if feedback_text else 'no'}")
    except Exception as e:
        logger.warning(f"[Supabase] Save failed: {e}")


class FeedbackRequest(BaseModel):
    feedback_text: str
    ticket_id: Optional[str] = None
    vehicle_id: Optional[str] = "WM-001"
    rating: Optional[int] = None


@app.post("/run-pipeline")
async def run_pipeline(request: FeedbackRequest):
    try:
        result = run_riderex_pipeline(
            feedback_text=request.feedback_text,
            ticket_id=request.ticket_id,
            vehicle_id=request.vehicle_id,
            rating=request.rating
        )
        save_to_supabase(result, feedback_text=request.feedback_text)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/metrics")
async def get_metrics(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    safety_level: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = 500,
):
    """Return ride records from Supabase for the dashboard."""
    sb = get_supabase()
    if not sb:
        return JSONResponse(status_code=503, content={"error": "Supabase not configured"})
    try:
        query = sb.table("rides").select(
            "id,ticket_id,ride_id,vehicle_id,vehicle_type,software_version,"
            "category,priority,safety_level,nhtsa,rating,churn_risk,"
            "refund_amount,credit_amount,good_ride,sentiment,quality_score,"
            "review_decision,requires_engineering,engineering_team,vehicle_action,"
            "action_items,band_messages,key_phrases,"
            "intake_data,resolution_data,review_data,created_at"
        ).order("created_at", desc=True).limit(limit)

        if category:   query = query.eq("category", category)
        if priority:   query = query.eq("priority", priority)
        if safety_level: query = query.eq("safety_level", safety_level)
        if days:
            from datetime import datetime, timedelta, timezone
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            query = query.gte("created_at", cutoff)

        res = query.execute()
        return JSONResponse(content={"rides": res.data, "total": len(res.data)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "RiderEx",
        "agents": 5,
        "band_configured": bool(os.getenv("BAND_API_KEY")),
        "aiml_configured": bool(os.getenv("AIML_API_KEY")),
        "supabase_configured": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY")),
    }


@app.get("/vehicles")
async def get_vehicles():
    try:
        with open("riderex_vehicles.json") as f:
            return JSONResponse(content=json.load(f))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


_INCIDENT_CAT = {
    'GNSS_DROPOUT':'SOFTWARE','SENSOR_FAILURE':'SAFETY','AEB_FALSE_TRIGGER':'SAFETY',
    'ROUTING_ERROR':'ROUTE','COMFORT_COMPLAINT':'COMFORT','SOFTWARE_BUG':'SOFTWARE',
    'LIDAR_INTERFERENCE':'SAFETY','PASSENGER_COMPLAINT':'COMFORT','MINOR_COLLISION':'SAFETY',
    'GPS_SPOOFING':'SAFETY','COMMUNICATION_LOSS':'SOFTWARE','BRAKE_ANOMALY':'SAFETY',
    'OBSTACLE_DETECTION':'SAFETY','LANE_DEPARTURE':'SAFETY','SPEED_REGULATION':'SOFTWARE',
    'CHARGING_FAILURE':'SOFTWARE','DOOR_MALFUNCTION':'COMFORT','CLIMATE_FAILURE':'COMFORT',
}
_VACTION = {'CRITICAL':'GROUND_VEHICLE','HIGH':'INSPECT_BEFORE_NEXT_RIDE','MEDIUM':'INSPECT_BEFORE_NEXT_RIDE','LOW':'CONTINUE_OPERATION','NONE':'CONTINUE_OPERATION'}
_ENG_TEAM = {'SAFETY':'AV_SAFETY','SOFTWARE':'SOFTWARE_TEAM','ROUTE':'LOCALIZATION_TEAM','COMFORT':'UX_TEAM','COMPLIMENT':'NONE'}
_CAT_POOL = ['SAFETY']*3+['COMFORT']*4+['SOFTWARE']*3+['ROUTE']*2+['COMPLIMENT']*3
_SL_FOR_CAT = {
    'SAFETY':['CRITICAL','HIGH','HIGH','MEDIUM','MEDIUM','LOW'],
    'COMFORT':['LOW','NONE','NONE','NONE'],
    'ROUTE':['LOW','LOW','MEDIUM','NONE'],
    'SOFTWARE':['NONE','NONE','LOW','MEDIUM'],
    'COMPLIMENT':['NONE'],
}

def _pick_priority(cat, sl):
    if sl == 'CRITICAL': return 'P1'
    if sl == 'HIGH': return 'P2'
    if cat in ('SAFETY','SOFTWARE'): return 'P3'
    if cat == 'COMPLIMENT': return 'P4'
    return 'P3' if random.random() < 0.4 else 'P4'

def _build_seed_records(vehicles):
    RIDES_PER_VEHICLE = 1252  # 200 × 1252 = 250,400 rides
    SPAN_DAYS = 365
    now = datetime.now(timezone.utc)
    records, idx = [], 0
    for v in vehicles:
        ss = v.get('safety_score', 90) or 90
        base_r = v.get('avg_passenger_rating', 4.0) or 4.0
        for ri in range(RIDES_PER_VEHICLE):
            days_ago = (ri / RIDES_PER_VEHICLE) * SPAN_DAYS + random.random() * (SPAN_DAYS / RIDES_PER_VEHICLE)
            ts = (now - timedelta(days=days_ago, hours=random.randint(0,23))).isoformat()
            if ri == 0:
                inc = v.get('last_incident_type')
                cat = ('COMPLIMENT' if base_r >= 4.5 else 'COMFORT') if (not inc or base_r >= 4.8) else _INCIDENT_CAT.get(inc,'SOFTWARE')
                sl  = 'CRITICAL' if ss<50 else 'HIGH' if ss<70 else 'MEDIUM' if ss<85 else 'LOW' if ss<95 else 'NONE'
            else:
                cat = random.choice(_CAT_POOL)
                sl  = random.choice(_SL_FOR_CAT[cat])
            priority = _pick_priority(cat, sl)
            rating   = min(5, max(1, round(base_r + (random.random()-0.5)*2)))
            churn    = 'HIGH' if rating<=2 else 'MEDIUM' if rating<=3 else 'LOW'
            sentiment= 'NEGATIVE' if rating<=2 else 'NEUTRAL' if rating<=3 else 'POSITIVE'
            qs       = min(100, max(48, round(58 + ss*0.25 + rating*3 + (random.random()-0.5)*12)))
            nhtsa    = sl=='CRITICAL' or (sl=='HIGH' and priority=='P1')
            req_eng  = cat in ('SAFETY','SOFTWARE') and sl!='NONE'
            refund   = random.randint(20,40) if priority=='P1' else random.randint(10,20) if priority=='P2' else 0
            credit   = 5 if cat=='COMPLIMENT' else random.randint(0,10) if priority=='P3' else 0
            records.append({
                'ticket_id': f'RX-{idx+1:06d}',
                'ride_id':   f'RIDE-{random.randint(1,9999999999999):016d}',
                'vehicle_id': v['vehicle_id'],
                'vehicle_type': v.get('model', '—'),
                'software_version': v.get('software_version', 'dawei-av-4.3.0'),
                'category': cat, 'priority': priority, 'safety_level': sl,
                'nhtsa': nhtsa, 'rating': rating, 'churn_risk': churn,
                'refund_amount': refund, 'credit_amount': credit,
                'good_ride': cat=='COMPLIMENT' or (sl=='NONE' and priority=='P4'),
                'sentiment': sentiment, 'quality_score': qs,
                'review_decision': 'APPROVED' if qs>=85 else 'APPROVED_WITH_EDITS' if qs>=72 else 'REVISION_NEEDED',
                'requires_engineering': req_eng,
                'engineering_team': _ENG_TEAM.get(cat,'NONE') if req_eng else 'NONE',
                'vehicle_action': _VACTION.get(sl,'CONTINUE_OPERATION'),
                'action_items': v.get('open_support_tickets', 0),
                'band_messages': random.randint(3,15),
                'key_phrases': [v['last_incident_type'].replace('_',' ')] if v.get('last_incident_type') else [],
                'intake_data': {}, 'safety_data': {}, 'resolution_data': {}, 'review_data': {}, 'engineering_data': {},
                'created_at': ts,
            })
            idx += 1
    return records


@app.post("/seed-supabase")
async def seed_supabase():
    """Bulk-insert 2000 seed ride records into Supabase (upserts on ticket_id)."""
    sb = get_supabase()
    if not sb:
        return JSONResponse(status_code=503, content={"error": "Supabase not configured"})
    try:
        with open("riderex_vehicles.json") as f:
            vehicles = json.load(f)
        records = _build_seed_records(vehicles)
        inserted = 0
        for i in range(0, len(records), 500):
            sb.table("rides").upsert(records[i:i+500], on_conflict="ticket_id").execute()
            inserted += min(500, len(records)-i)
        logger.info(f"[Seed] Inserted {inserted} records into Supabase")
        return JSONResponse(content={"inserted": inserted, "total": len(records)})
    except Exception as e:
        logger.error(f"[Seed] Failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/clean-bad-vehicles")
async def clean_bad_vehicles():
    """Delete Supabase records whose vehicle_id is not in WM-001..WM-200."""
    sb = get_supabase()
    if not sb:
        return JSONResponse(status_code=503, content={"error": "Supabase not configured"})
    try:
        valid_ids = [f"WM-{str(i).zfill(3)}" for i in range(1, 201)]
        res = sb.table("rides").delete().not_.in_("vehicle_id", valid_ids).execute()
        deleted = len(res.data) if res.data else 0
        logger.info(f"[Clean] Deleted {deleted} records with invalid vehicle IDs")
        return JSONResponse(content={"deleted": deleted})
    except Exception as e:
        logger.error(f"[Clean] Failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html").read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
