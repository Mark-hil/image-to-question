const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "/api" : "http://localhost:8000/api");

import type { EducationCatalogResponse, LevelResolveResponse } from '../types/education';

export interface QuestionData {
  id?: string;
  question_text?: string;
  question?: string;
  answer_text?: string;
  answer?: string;
  choices?: string[];
  rationale?: string;
  qtype?: string;
  difficulty?: string;
  blooms_level?: string;
  class_id?: string;
  education_level?: string;
  class_label?: string;
  subject?: string;
}

export interface QuizData {
  id: string;
  title: string;
  subject: string;
  class_id?: string;
  education_level?: string;
  class_label?: string;
  original_file_name?: string;
  question_count: number;
  created_at: string;
  questions?: QuestionData[];
}

let educationCatalogCache: EducationCatalogResponse | null = null;

export const api = {
  // Education Levels Catalog
  async getEducationLevels(): Promise<EducationCatalogResponse> {
    if (educationCatalogCache) {
      return educationCatalogCache;
    }
    const res = await fetch(`${API_BASE_URL}/education-levels`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to fetch education levels");
    educationCatalogCache = data as EducationCatalogResponse;
    return educationCatalogCache;
  },

  async resolveEducationLevel(query: string): Promise<LevelResolveResponse> {
    const res = await fetch(`${API_BASE_URL}/education-levels/resolve?query=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to resolve education level");
    return data as LevelResolveResponse;
  },

  // Auth
  async register(email: string, password: string, fullName?: string) {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");
    return data;
  },

  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    return data;
  },

  async getMe(token: string) {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to fetch user");
    return data.user;
  },

  // Question Generation
  async uploadAndGenerate(
    files: File | File[],
    qtype: string = "mcq",
    difficulty: string = "medium",
    numQuestions: number = 3,
    subject: string = "General",
    apiKey?: string,
    classId?: string,
    bloomsLevel: string = "all",
    pageRange: string = "",
    mode: string = "exam",
    educationLevel?: string,
    classLabel?: string
  ) {
    const formData = new FormData();
    const fileList = Array.isArray(files) ? files : [files];
    fileList.forEach(file => {
      formData.append("files", file);
    });
    formData.append("qtype", qtype);
    formData.append("difficulty", difficulty);
    formData.append("blooms_level", bloomsLevel);
    formData.append("num_questions", numQuestions.toString());
    formData.append("subject", subject);
    formData.append("mode", mode);
    if (pageRange) formData.append("page_range", pageRange);
    if (classId) formData.append("class_id", classId);
    if (educationLevel) formData.append("education_level", educationLevel);
    if (classLabel) formData.append("class_label", classLabel);

    const headers: Record<string, string> = {};
    if (apiKey) {
      headers["X-API-Key"] = apiKey;
    }
    const token = localStorage.getItem("qgen_jwt_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const queryParamsObj: Record<string, string> = {
      qtype,
      difficulty,
      blooms_level: bloomsLevel,
      num_questions: numQuestions.toString(),
      subject: subject || "General",
      mode: mode || "exam",
    };
    if (pageRange) queryParamsObj.page_range = pageRange;
    if (classId) queryParamsObj.class_id = classId;
    if (educationLevel) queryParamsObj.education_level = educationLevel;
    if (classLabel) queryParamsObj.class_label = classLabel;

    const queryParams = new URLSearchParams(queryParamsObj).toString();

    const res = await fetch(`${API_BASE_URL}/generate/upload-and-generate?${queryParams}`, {
      method: "POST",
      headers,
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Question generation failed");
    const questions = (data.questions || []) as (QuestionData[] & { usage?: any; limit_hit_warning?: string });
    (questions as any).usage = data.usage;
    (questions as any).limit_hit_warning = data.limit_hit_warning;
    return questions;
  },

  // Quizzes
  async saveQuiz(
    token: string,
    title: string,
    subject: string,
    originalFileName: string | undefined,
    questions: QuestionData[],
    classId?: string,
    educationLevel?: string,
    classLabel?: string
  ) {
    const normalizedQuestions = questions.map((q) => ({
      question_text: q.question_text || q.question || '',
      answer_text: q.answer_text || q.answer || '',
      choices: q.choices || [],
      rationale: q.rationale || '',
      qtype: q.qtype || 'mcq',
      difficulty: q.difficulty || 'medium',
      blooms_level: q.blooms_level || 'Understand',
      class_id: q.class_id || classId,
      education_level: q.education_level || educationLevel,
      class_label: q.class_label || classLabel,
    }));

    const res = await fetch(`${API_BASE_URL}/quizzes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        title,
        subject,
        class_id: classId,
        education_level: educationLevel,
        class_label: classLabel,
        original_file_name: originalFileName,
        questions: normalizedQuestions,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to save quiz");
    return data.quiz as QuizData;
  },

  async listQuizzes(token: string, filter?: { educationLevel?: string; stage?: string }) {
    let url = `${API_BASE_URL}/quizzes`;
    const params = new URLSearchParams();
    if (filter?.educationLevel) params.append("education_level", filter.educationLevel);
    if (filter?.stage) params.append("stage", filter.stage);
    const qs = params.toString();
    if (qs) url += `?${qs}`;

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to fetch quizzes");
    return data.quizzes as QuizData[];
  },

  async updateQuestion(
    token: string,
    quizId: string,
    questionId: string,
    updates: Partial<QuestionData>
  ) {
    const res = await fetch(`${API_BASE_URL}/quizzes/${quizId}/questions/${questionId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update question");
    return data.question;
  },

  async deleteQuiz(token: string, quizId: string) {
    const res = await fetch(`${API_BASE_URL}/quizzes/${quizId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to delete quiz");
    return data;
  },

  async bulkDeleteQuizzes(token: string, quizIds: string[]) {
    const res = await fetch(`${API_BASE_URL}/quizzes/bulk-delete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ quiz_ids: quizIds }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to bulk delete quizzes");
    return data;
  },

  async bulkExportQuizzes(token: string, quizIds: string[], format: "csv" | "docx" | "qti" | "text" = "csv") {
    const filename = `QGen_Bulk_Export_${quizIds.length}_quizzes.zip`;
    const res = await fetch(`${API_BASE_URL}/quizzes/bulk-export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ quiz_ids: quizIds, export_format: format }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: "Bulk export failed" }));
      throw new Error(errData.detail || "Failed to bulk export quizzes.");
    }

    const blobData = await res.blob();
    const fileBlob = new Blob([blobData], { type: "application/zip" });
    const url = window.URL.createObjectURL(fileBlob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.setAttribute("download", filename);
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      if (document.body.contains(a)) document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 200);
  },

  getQtiExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/qti`;
  },

  getTextExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/text`;
  },

  getDocxExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/docx`;
  },

  getCsvExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/csv`;
  },

  async exportDirect(title: string, questions: QuestionData[], format: "qti" | "text" | "docx" | "csv" = "docx") {
    const safeTitle = (title || "Quiz_Bank").replace(/[^a-zA-Z0-9_\-]/g, "_");
    let extension = ".docx";
    let mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    if (format === "qti") {
      extension = "_qti.zip";
      mimeType = "application/zip";
    } else if (format === "text") {
      extension = ".txt";
      mimeType = "text/plain";
    } else if (format === "csv") {
      extension = ".csv";
      mimeType = "text/csv";
    }

    const filename = `${safeTitle}${extension}`;

    const res = await fetch(`${API_BASE_URL}/quizzes/export/direct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: safeTitle,
        export_format: format,
        questions,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: "Export failed" }));
      throw new Error(errData.detail || "Failed to generate export file.");
    }

    const blobData = await res.blob();
    const fileBlob = new Blob([blobData], { type: mimeType });
    const url = window.URL.createObjectURL(fileBlob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.setAttribute("download", filename);
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      if (document.body.contains(a)) document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 200);
  },

  async exportQuiz(token: string, quizId: string, format: "qti" | "text" | "docx" | "csv" = "docx", title?: string) {
    const safeTitle = (title || "Quiz_Bank").replace(/[^a-zA-Z0-9_\-]/g, "_");
    let extension = ".docx";
    let mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    if (format === "qti") {
      extension = "_qti.zip";
      mimeType = "application/zip";
    } else if (format === "text") {
      extension = ".txt";
      mimeType = "text/plain";
    } else if (format === "csv") {
      extension = ".csv";
      mimeType = "text/csv";
    }

    const filename = `${safeTitle}${extension}`;

    const res = await fetch(`${API_BASE_URL}/quizzes/${quizId}/export/${format}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: "Download failed" }));
      throw new Error(errData.detail || "Failed to download export file.");
    }

    const blobData = await res.blob();
    const fileBlob = new Blob([blobData], { type: mimeType });
    const url = window.URL.createObjectURL(fileBlob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.setAttribute("download", filename);
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      if (document.body.contains(a)) document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 200);
  },



  // Paystack Billing
  async initializePayment(email: string, amount: number, tenantId?: string, userId?: string, planTier?: string) {
    const res = await fetch(`${API_BASE_URL}/billing/initialize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, amount, tenant_id: tenantId, user_id: userId, plan_tier: planTier }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to initialize payment");
    return data;
  },

  // Async Background Task Pipeline
  async generateAsync(
    files: File | File[],
    qtype: string = "mcq",
    difficulty: string = "medium",
    numQuestions: number = 3,
    subject: string = "General",
    apiKey?: string,
    bloomsLevel: string = "all",
    pageRange: string = "",
    mode: string = "exam",
    classId?: string,
    educationLevel?: string,
    classLabel?: string
  ): Promise<{ task_id: string; status: string; progress: number; stage: string }> {
    const formData = new FormData();
    const fileList = Array.isArray(files) ? files : [files];
    fileList.forEach(file => {
      formData.append("files", file);
    });
    formData.append("qtype", qtype);
    formData.append("difficulty", difficulty);
    formData.append("blooms_level", bloomsLevel);
    formData.append("num_questions", numQuestions.toString());
    formData.append("subject", subject);
    formData.append("mode", mode);
    if (pageRange) formData.append("page_range", pageRange);
    if (classId) formData.append("class_id", classId);
    if (educationLevel) formData.append("education_level", educationLevel);
    if (classLabel) formData.append("class_label", classLabel);

    const headers: Record<string, string> = {};
    if (apiKey) {
      headers["X-API-Key"] = apiKey;
    }
    const token = localStorage.getItem("qgen_jwt_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const queryParamsObj: Record<string, string> = {
      qtype,
      difficulty,
      blooms_level: bloomsLevel,
      num_questions: numQuestions.toString(),
      subject: subject || "General",
      mode: mode || "exam",
    };
    if (pageRange) queryParamsObj.page_range = pageRange;
    if (classId) queryParamsObj.class_id = classId;
    if (educationLevel) queryParamsObj.education_level = educationLevel;
    if (classLabel) queryParamsObj.class_label = classLabel;

    const queryParams = new URLSearchParams(queryParamsObj).toString();

    const res = await fetch(`${API_BASE_URL}/tasks/generate-async?${queryParams}`, {
      method: "POST",
      headers,
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to start async task.");
    return data;
  },

  async getTaskStatus(taskId: string): Promise<{
    task_id: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    progress: number;
    stage: string;
    questions?: QuestionData[];
    usage?: any;
    limit_hit_warning?: string;
    error?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/tasks/status/${taskId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to fetch task status.");
    return data;
  },

  async inspectPdf(file: File): Promise<{
    total_pages: number;
    chapters: Array<{
      title: string;
      level: number;
      start_page: number;
      end_page: number;
      range: string;
    }>;
  }> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE_URL}/generate/inspect-pdf`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to inspect PDF.");
    return data;
  },

  // Tenant & B2B Developer API Key Management
  async registerTenant(name: string, email: string, tier: string = "free") {
    const res = await fetch(`${API_BASE_URL}/tenants/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, tier }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Tenant registration failed.");
    return data;
  },

  async createApiKey(tenantId: string, name: string = "Default Key", rateLimitRpm: number = 60) {
    const res = await fetch(`${API_BASE_URL}/tenants/${tenantId}/api-keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, rate_limit_rpm: rateLimitRpm }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to create API key.");
    return data.api_key;
  },

  async listApiKeys(tenantId: string) {
    const res = await fetch(`${API_BASE_URL}/tenants/${tenantId}/api-keys`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to list API keys.");
    return data.api_keys;
  },

  async revokeApiKey(tenantId: string, keyId: string) {
    const res = await fetch(`${API_BASE_URL}/tenants/${tenantId}/api-keys/${keyId}`, {
      method: "DELETE",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to revoke API key.");
    return data;
  },

  async getTenantUsage(tenantId: string) {
    const res = await fetch(`${API_BASE_URL}/tenants/${tenantId}/usage`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Failed to fetch tenant usage.");
    return data;
  },
};


