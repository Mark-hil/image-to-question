const API_BASE_URL = "http://localhost:8000/api";

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
  subject?: string;
}

export interface QuizData {
  id: string;
  title: string;
  subject: string;
  original_file_name?: string;
  question_count: number;
  created_at: string;
  questions?: QuestionData[];
}

export const api = {
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
    file: File,
    qtype: string = "mcq",
    difficulty: string = "medium",
    numQuestions: number = 3,
    subject: string = "General",
    apiKey?: string
  ) {
    const formData = new FormData();
    formData.append("files", file);
    formData.append("qtype", qtype);
    formData.append("difficulty", difficulty);
    formData.append("num_questions", numQuestions.toString());
    formData.append("subject", subject);

    const headers: Record<string, string> = {};
    if (apiKey) {
      headers["X-API-Key"] = apiKey;
    }

    const queryParams = new URLSearchParams({
      qtype,
      difficulty,
      num_questions: numQuestions.toString(),
      subject: subject || "General",
    }).toString();

    const res = await fetch(`${API_BASE_URL}/generate/upload-and-generate?${queryParams}`, {
      method: "POST",
      headers,
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.detail || "Question generation failed");
    return data.questions as QuestionData[];
  },

  // Quizzes
  async saveQuiz(
    token: string,
    title: string,
    subject: string,
    originalFileName: string | undefined,
    questions: QuestionData[]
  ) {
    const normalizedQuestions = questions.map((q) => ({
      question_text: q.question_text || q.question || '',
      answer_text: q.answer_text || q.answer || '',
      choices: q.choices || [],
      rationale: q.rationale || '',
      qtype: q.qtype || 'mcq',
      difficulty: q.difficulty || 'medium',
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
        original_file_name: originalFileName,
        questions: normalizedQuestions,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to save quiz");
    return data.quiz as QuizData;
  },

  async listQuizzes(token: string) {
    const res = await fetch(`${API_BASE_URL}/quizzes`, {
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

  getQtiExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/qti`;
  },

  getTextExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/text`;
  },

  getDocxExportUrl(quizId: string) {
    return `${API_BASE_URL}/quizzes/${quizId}/export/docx`;
  },

  async exportDirect(title: string, questions: QuestionData[], format: "qti" | "text" | "docx" = "docx") {
    const safeTitle = (title || "Quiz_Bank").replace(/[^a-zA-Z0-9_\-]/g, "_");
    let extension = ".docx";
    let mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    if (format === "qti") {
      extension = "_qti.zip";
      mimeType = "application/zip";
    } else if (format === "text") {
      extension = ".txt";
      mimeType = "text/plain";
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

  async exportQuiz(token: string, quizId: string, format: "qti" | "text" | "docx" = "docx", title?: string) {
    const safeTitle = (title || "Quiz_Bank").replace(/[^a-zA-Z0-9_\-]/g, "_");
    let extension = ".docx";
    let mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    if (format === "qti") {
      extension = "_qti.zip";
      mimeType = "application/zip";
    } else if (format === "text") {
      extension = ".txt";
      mimeType = "text/plain";
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
  async initializePayment(email: string, amount: number, tenantId?: string) {
    const res = await fetch(`${API_BASE_URL}/billing/initialize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, amount, tenant_id: tenantId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to initialize payment");
    return data;
  },
};
