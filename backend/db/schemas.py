from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InterviewStart(BaseModel):
    role: str
    difficulty: Optional[str] = "medium"
    knowledge_points: Optional[List[str]] = []
    total_rounds: Optional[int] = 5
    repo_urls: Optional[List[str]] = []   # v3: GitHub 项目深挖（可选，≤3 个）


class RepoAnalyzeRequest(BaseModel):
    url: str


class RepoSummary(BaseModel):
    owner: str
    name: str
    full_name: str
    url: str
    description: Optional[str] = ""
    main_language: Optional[str] = ""
    languages: dict = {}
    stars: int = 0
    readme_excerpt: str = ""
    tech_keywords: List[str] = []
    top_level_files: List[str] = []
    recent_commits: List[dict] = []

class InterviewResponse(BaseModel):
    id: int
    user_id: int
    role: str
    status: str
    start_time: datetime
    class Config:
        from_attributes = True

class MessageSend(BaseModel):
    content: str
    # audio path omitted for MVP simplicity handled via multipart if needed

class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    created_at: datetime
    is_final: bool = False
    class Config:
        from_attributes = True

class EvaluationSummary(BaseModel):
    id: int
    role: str
    difficulty: str
    total_score: float
    created_at: datetime
    class Config:
        from_attributes = True

class EvaluationDetail(BaseModel):
    interview_id: int
    role: str
    content_score: float
    expression_score: float
    business_scenario_score: float
    problem_solving_score: float
    total_score: float
    highlights: List[str]
    weaknesses: List[str]
    recommendations: str
    scores: Optional[dict] = None
    # —— 表达分析三维子分（v2 新增） ——
    speech_rate_score: Optional[float] = 0.0
    clarity_score: Optional[float] = 0.0
    confidence_score: Optional[float] = 0.0
    expression_metrics: Optional[dict] = None 
    # —— v3: GitHub 项目深挖（列表） ——
    repo_context: Optional[List[dict]] = None      
    custom_questions: Optional[List[dict]] = None   
    # —— 能力提升反馈 ——
    study_plan: Optional[dict] = None               
    created_at: datetime

class VoiceResponse(BaseModel):
    transcription: str
    ai_message: MessageResponse
