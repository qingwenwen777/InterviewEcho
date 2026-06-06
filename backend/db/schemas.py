from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
    repo_summaries: Optional[List[dict]] = []  # 前端预分析结果，开始面试时优先复用


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
    round_index: Optional[int] = None
    question_id: Optional[str] = None
    parent_question_id: Optional[int] = None
    action: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    is_final: bool = False
    class Config:
        from_attributes = True

class EvaluationSummary(BaseModel):
    id: int
    role: str
    difficulty: Optional[str] = None
    total_score: Optional[float] = None
    status: str = "completed"
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
    user_message: Optional[MessageResponse] = None
    ai_message: Optional[MessageResponse] = None
    reply_status: str = "processing"


class TTSRequest(BaseModel):
    voice: Optional[str] = "mimo_default"
    speed: Optional[str] = "normal"
    style: Optional[str] = "calm"


class TTSResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"
    format: str = "wav"
    voice: str = "mimo_default"


class ProfileResumeUpdate(BaseModel):
    display_name: Optional[str] = None
    headline: Optional[str] = None
    target_role: Optional[str] = None
    resume_text: Optional[str] = None
    use_ai: bool = True


class UserProfileData(BaseModel):
    id: Optional[int] = None
    display_name: str = ""
    headline: str = ""
    target_role: str = ""
    resume_filename: str = ""
    resume_text: str = ""
    resume_summary: str = ""
    skills: List[str] = []
    education: List[str] = []
    experience: List[str] = []
    projects: List[str] = []
    updated_at: Optional[datetime] = None


class UserProjectCreate(BaseModel):
    url: str


class UserProjectItem(BaseModel):
    id: int
    url: str
    full_name: str
    name: str = ""
    description: str = ""
    main_language: str = ""
    stars: int = 0
    tech_keywords: List[str] = []
    summary: Dict[str, Any] = {}
    updated_at: Optional[datetime] = None


class UserProfileResponse(BaseModel):
    profile: UserProfileData
    projects: List[UserProjectItem] = []


class CodeProblemListItem(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: str
    tags: List[str]
    source: str = "Hot100"
    solved: bool = False
    judgable: bool = False
    sample_count: int = 0
    test_count: int = 0


class CodeProblemDetail(CodeProblemListItem):
    description: str
    input_format: str
    output_format: str
    samples: List[Dict[str, Any]]
    constraints: List[str]
    starter_code: Dict[str, str]


class CodeProblemListResponse(BaseModel):
    items: List[CodeProblemListItem]
    tags: List[str]
    total: int


class CodeRunRequest(BaseModel):
    language: str
    source_code: str


class CodeCaseResult(BaseModel):
    index: int
    is_sample: bool
    passed: bool
    status: str
    status_description: Optional[str] = None
    input: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    runtime: Optional[float] = None
    memory: Optional[int] = None
    message: Optional[str] = None


class CodeRunResponse(BaseModel):
    status: str
    passed_count: int
    total_count: int
    results: List[CodeCaseResult]


class CodeSubmitResponse(CodeRunResponse):
    submission_id: int


class CodeSubmissionItem(BaseModel):
    id: int
    problem_id: int
    problem_title: Optional[str] = None
    language: str
    status: str
    runtime: Optional[float] = None
    memory: Optional[int] = None
    passed_count: int
    total_count: int
    created_at: datetime


class CodeSubmissionDetail(CodeSubmissionItem):
    source_code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    results: Optional[List[CodeCaseResult]] = None
