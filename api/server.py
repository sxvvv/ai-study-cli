"""FastAPI Backend - REST API wrapping ai-study-cli modules"""
import os
import sys

# 确保项目根目录在path中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from tracker import (
    get_progress, save_progress, mark_done, mark_skip,
    get_current_day, get_phase_info, start_if_needed,
    is_open_mode, get_days_until_job, TOTAL_DAYS,
    record_streak_layer, check_micro_achieved
)
from planner import get_today_tasks, get_today_summary_for_push
from quiz import get_quiz_questions, record_quiz_result, get_quiz_stats
from flashcard import (
    get_due_cards, review_card, find_card, get_flashcard_stats,
    add_flashcard
)
from fetcher import fetch_daily_recommendations, format_recommendations
from resources import get_phase_resources, add_custom_resource
from skillmap import (
    get_skill_map, get_all_skills, get_skill_gaps,
    get_skill_progress_summary, update_skill_level,
    map_repo_to_skill, format_skill_map
)
from notifier import push_telegram, send_daily_reminder
from github_sync import get_starred_with_skills

app = FastAPI(
    title="AI Study CLI API",
    description="AI Inference Acceleration Engineer Skill Mastery System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Progress & Streak ===

@app.get("/api/progress")
def api_progress():
    progress = get_progress()
    progress = start_if_needed(progress)
    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)
    return {
        "progress": progress,
        "current_day": current_day,
        "phase_info": phase_info,
        "days_until_job": get_days_until_job(),
        "is_open_mode": is_open_mode(current_day),
    }


@app.get("/api/streak")
def api_streak():
    progress = get_progress()
    progress = start_if_needed(progress)
    micro_done = check_micro_achieved(progress)
    return {
        "streak": progress.get("streak", 0),
        "max_streak": progress.get("max_streak", 0),
        "streak_layer": progress.get("streak_layer", "none"),
        "micro_achieved_today": micro_done,
    }


@app.post("/api/streak/record")
def api_record_streak_layer(layer: str = Query(..., regex="^(micro|plan|demo)$")):
    result = record_streak_layer(layer)
    return {"message": result}


@app.post("/api/tasks/{task_id}/done")
def api_mark_done(task_id: str):
    progress = get_progress()
    success, msg = mark_done(progress, task_id)
    return {"success": success, "message": msg}


@app.post("/api/tasks/{task_id}/skip")
def api_mark_skip(task_id: str, reason: str = ""):
    progress = get_progress()
    success, msg = mark_skip(progress, task_id, reason)
    return {"success": success, "message": msg}


# === Daily Tasks ===

@app.get("/api/daily-tasks")
def api_daily_tasks():
    output, error = get_today_tasks()
    if error:
        return {"error": error}
    return {"tasks": output}


@app.get("/api/daily-summary")
def api_daily_summary():
    content = get_today_summary_for_push()
    return {"summary": content}


# === Quiz ===

@app.get("/api/quizzes")
def api_quizzes(count: int = Query(3, ge=1, le=10)):
    questions, error = get_quiz_questions(count)
    if error:
        return {"error": error, "questions": []}
    return {"questions": questions}


@app.post("/api/quiz/answer")
def api_quiz_answer(quiz_id: str = Query(...), confidence: str = Query(..., regex="^(understand|fuzzy|not_understand)$")):
    record_quiz_result(quiz_id, confidence)
    progress = get_progress()
    today_str = progress.get("daily_logs", {})
    return {
        "message": f"已记录: {quiz_id} → {confidence}",
        "quiz_stats": get_quiz_stats(progress),
    }


# === Flashcards ===

@app.get("/api/flashcards")
def api_flashcards(count: int = Query(5, ge=1, le=20)):
    cards = get_due_cards(count)
    return {"cards": cards, "count": len(cards)}


@app.get("/api/flashcards/{card_id}")
def api_flashcard_detail(card_id: str):
    card = find_card(card_id)
    if not card:
        return {"error": f"闪卡 {card_id} 不存在"}
    return {"card": card}


@app.post("/api/flashcard/review")
def api_flashcard_review(card_id: str = Query(...), remembered: bool = Query(...)):
    result = review_card(card_id, remembered)
    return {"message": result}


@app.get("/api/flashcard/stats")
def api_flashcard_stats():
    stats = get_flashcard_stats()
    return stats


# === Feed ===

@app.get("/api/feed")
def api_feed(force_refresh: bool = False):
    data = fetch_daily_recommendations(force_refresh=force_refresh)
    return {"data": data, "formatted": format_recommendations(data)}


# === Resources ===

@app.get("/api/resources")
def api_resources():
    return {"resources": get_phase_resources()}


@app.post("/api/resources/add")
def api_add_resource(url: str = Query(...), tag: str = ""):
    result = add_custom_resource(url, tag)
    return {"message": result}


# === Skill Map ===

@app.get("/api/skillmap")
def api_skillmap():
    return get_skill_map()


@app.get("/api/skillmap/summary")
def api_skillmap_summary():
    return get_skill_progress_summary()


@app.get("/api/skillmap/gaps")
def api_skillmap_gaps():
    gaps = get_skill_gaps()
    return {"gaps": gaps, "count": len(gaps)}


@app.post("/api/skillmap/{skill_id}/level")
def api_update_skill_level(skill_id: str, level: int = Query(..., ge=0, le=5)):
    success = update_skill_level(skill_id, level)
    return {"success": success, "skill_id": skill_id, "level": level}


@app.get("/api/skillmap/repo-map")
def api_repo_map(repo: str = Query(...)):
    skills = map_repo_to_skill(repo)
    return {"repo": repo, "matched_skills": skills}


# === Notifications ===

@app.post("/api/notify/daily")
def api_notify_daily():
    result = send_daily_reminder()
    return {"result": result}


@app.post("/api/notify/telegram")
def api_notify_telegram(title: str = Query(...), content: str = Query(...)):
    ok, msg = push_telegram(title, content)
    return {"success": ok, "message": msg}


# === GitHub Stars ===

@app.get("/api/github/stars")
def api_github_stars():
    repos, error = get_starred_with_skills()
    if error:
        return {"error": error, "repos": []}
    return {"repos": repos, "count": len(repos)}


# === Health ===

@app.get("/api/health")
def api_health():
    return {"status": "ok", "version": "2.0.0"}


def run_server(host="0.0.0.0", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
