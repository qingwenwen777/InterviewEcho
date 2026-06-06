from sqlalchemy import Boolean, Column, Integer, String, Text, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    display_name = Column(String(80), nullable=True)
    headline = Column(String(160), nullable=True)
    target_role = Column(String(80), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=True)
    resume_summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class UserProject(Base):
    __tablename__ = "user_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(255), nullable=False)
    full_name = Column(String(160), nullable=False)
    name = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    main_language = Column(String(80), nullable=True)
    stars = Column(Integer, default=0)
    tech_keywords = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    reference_answer = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=True)
    knowledge_points = Column(Text, nullable=True) # Stored as JSON string
    total_rounds = Column(Integer, default=5)
    status = Column(String(20), default="in_progress")
    start_time = Column(TIMESTAMP, default=datetime.utcnow)
    end_time = Column(TIMESTAMP, nullable=True)
    # —— GitHub 项目深挖（v3 新增，参见 GitHub_Deep_Dive_Plan.md） ——
    repo_context = Column(Text, nullable=True)      # JSON list：各 repo 的抓取摘要（≤ 3 个）
    custom_questions = Column(Text, nullable=True)  # JSON list：LLM 针对 repos 生成的定制问题

    user = relationship("User")
    evaluations = relationship("Evaluation", uselist=False, back_populates="interview")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True) # For evaluation alignment
    round_index = Column(Integer, nullable=True)
    question_id = Column(String(160), nullable=True)
    parent_question_id = Column(Integer, nullable=True)
    action = Column(String(30), nullable=True)
    source = Column(String(50), nullable=True)
    audio_path = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True)
    content_score = Column(Float, default=0.0)
    expression_score = Column(Float, default=0.0)
    business_scenario_score = Column(Float, default=0.0)
    problem_solving_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    # —— 表达分析三维子分（v2 新增，参见 docs/expression_module_contract.md） ——
    speech_rate_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    report_json = Column(Text)
    recommendations = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="evaluations")


class VoiceMetrics(Base):
    """单条用户语音回答的声学/语言特征。
    由 services.audio_analysis.analyze_audio() 产出，
    在 end_interview 时由 evaluation.expression_evaluator 聚合。
    """
    __tablename__ = "voice_metrics"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    duration_sec = Column(Float)
    wpm = Column(Float)
    pause_ratio = Column(Float)
    long_pause_count = Column(Integer, default=0)
    filler_total = Column(Integer, default=0)
    pitch_mean = Column(Float)
    pitch_std = Column(Float)
    volume_mean = Column(Float)
    volume_std = Column(Float)
    raw_json = Column(Text)  # 完整 VoiceMetrics dict（含 segments、filler 明细）
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class CodeProblem(Base):
    __tablename__ = "code_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    difficulty = Column(String(20), nullable=False)
    tags = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    input_format = Column(Text, nullable=False)
    output_format = Column(Text, nullable=False)
    samples = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    source = Column(String(50), default="Hot100")
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_cases = relationship("CodeTestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("CodeSubmission", back_populates="problem")


class CodeTestCase(Base):
    __tablename__ = "code_test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("code_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    problem = relationship("CodeProblem", back_populates="test_cases")


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("code_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(30), nullable=False)
    source_code = Column(Text, nullable=False)
    status = Column(String(40), nullable=False)
    runtime = Column(Float, nullable=True)
    memory = Column(Integer, nullable=True)
    passed_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User")
    problem = relationship("CodeProblem", back_populates="submissions")
