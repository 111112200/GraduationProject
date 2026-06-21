from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Course, Clazz, Experiment, Report, CheckTask, User

router = APIRouter()


class CourseCreate(BaseModel):
    name: str
    code: str = ""


class ClazzCreate(BaseModel):
    name: str
    grade: str = ""


class ExperimentCreate(BaseModel):
    courseId: int
    title: str
    description: str = ""


@router.get("/courses")
async def api_get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    return {"courses": [{"id": c.id, "name": c.name, "code": c.code} for c in courses]}


@router.post("/courses")
async def api_create_course(body: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = Course(name=body.name, code=body.code or None, user_id=current_user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@router.get("/classes")
async def api_get_classes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    classes = db.query(Clazz).filter(Clazz.user_id == current_user.id).all()
    result = []
    for c in classes:
        report_count = db.query(Report).filter(Report.class_id == c.id, Report.user_id == current_user.id).count()
        result.append({"id": c.id, "name": c.name, "grade": c.grade, "reportCount": report_count})
    return {"classes": result}


@router.post("/classes")
async def api_create_clazz(body: ClazzCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = Clazz(name=body.name, grade=body.grade or None, user_id=current_user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@router.delete("/classes/{class_id}")
async def api_delete_clazz(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Clazz).filter(Clazz.id == class_id, Clazz.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="班级不存在")
    report_count = db.query(Report).filter(Report.class_id == class_id, Report.user_id == current_user.id).count()
    if report_count > 0:
        raise HTTPException(status_code=400, detail=f"该班级下仍有 {report_count} 份报告，无法删除")
    db.delete(c)
    db.commit()
    return {"success": True}


@router.get("/experiments")
async def api_get_experiments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exps = db.query(Experiment).filter(Experiment.user_id == current_user.id).all()
    return {"experiments": [{"id": e.id, "courseId": e.course_id, "title": e.title} for e in exps]}


@router.post("/experiments")
async def api_create_experiment(body: ExperimentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify course belongs to user
    course = db.query(Course).filter(Course.id == body.courseId, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
        
    e = Experiment(course_id=body.courseId, title=body.title, description=body.description or None, user_id=current_user.id)
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "title": e.title}


@router.delete("/experiments/{experiment_id}")
async def api_delete_experiment(experiment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = db.query(Experiment).filter(Experiment.id == experiment_id, Experiment.user_id == current_user.id).first()
    if not e:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    report_count = db.query(Report).filter(Report.experiment_id == experiment_id, Report.user_id == current_user.id).count()
    if report_count > 0:
        raise HTTPException(status_code=400, detail=f"该实验下仍有 {report_count} 份报告，无法删除")
        
    task_count = db.query(CheckTask).filter(CheckTask.experiment_id == experiment_id, CheckTask.user_id == current_user.id).count()
    if task_count > 0:
        raise HTTPException(status_code=400, detail=f"该实验下仍有 {task_count} 个查重任务，无法删除")
        
    db.delete(e)
    db.commit()
    return {"success": True}
