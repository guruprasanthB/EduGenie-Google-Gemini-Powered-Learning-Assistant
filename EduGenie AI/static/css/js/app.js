const tools = {
	qa: {
		title: "Ask a question",
		description: "Get a clear, considered answer with the important ideas up front.",
		action: "Get an answer",
		endpoint: "/qa",
		fields: [
			{ name: "question", label: "What would you like to understand?", type: "textarea", placeholder: "Ask about a topic, idea, or problem...", required: true }
		]
	},
	explain: {
		title: "Explain a concept",
		description: "Build an explanation around your current level of understanding.",
		action: "Explain concept",
		endpoint: "/explain",
		fields: [
			{ name: "topic", label: "Concept or topic", type: "input", placeholder: "For example, natural selection", required: true },
			{ name: "level", label: "Explanation level", type: "select", options: [["beginner", "Beginner"], ["intermediate", "Intermediate"], ["advanced", "Advanced"]] }
		]
	},
	quiz: {
		title: "Create a quiz",
		description: "Turn your notes into questions with answers and explanations.",
		action: "Build quiz",
		endpoint: "/quiz",
		fields: [
			{ name: "text", label: "Study material", type: "textarea", placeholder: "Paste a passage or your study notes...", required: true, minLength: 40 },
			{ name: "question_count", label: "Number of questions", type: "select", options: [["3", "3 questions"], ["5", "5 questions"], ["8", "8 questions"]] }
		]
	},
	summarize: {
		title: "Summarize notes",
		description: "Pull the key ideas from a passage into a useful study summary.",
		action: "Make summary",
		endpoint: "/summarize",
		fields: [
			{ name: "text", label: "Text to summarize", type: "textarea", placeholder: "Paste an article, chapter, or class notes...", required: true },
			{ name: "style", label: "Summary style", type: "select", options: [["concise", "Concise"], ["detailed", "Detailed"], ["bullet_points", "Bullet points"]] }
		]
	},
	learn: {
		title: "Plan a learning path",
		description: "Get a sequenced plan with milestones and practice ideas.",
		action: "Create learning path",
		endpoint: "/learn/recommendations",
		fields: [
			{ name: "topic", label: "What do you want to learn?", type: "input", placeholder: "For example, conversational Spanish", required: true },
			{ name: "level", label: "Starting level", type: "select", options: [["beginner", "Beginner"], ["intermediate", "Intermediate"], ["advanced", "Advanced"]] },
			{ name: "duration", label: "Time available", type: "select", options: [["2", "2 weeks"], ["4", "4 weeks"], ["8", "8 weeks"]] }
		]
	}
};

const form = document.querySelector("#study-form");
const fieldsContainer = document.querySelector("#form-fields");
const resultContent = document.querySelector("#result-content");
const outputPanel = document.querySelector(".output-panel");
const submitButton = document.querySelector("#submit-button");
const submitLabel = document.querySelector("#submit-label");
const copyButton = document.querySelector("#copy-button");
let activeMode = "qa";
let latestResult = "";
const formDrafts = {};

function renderFields(fields) {
	fieldsContainer.replaceChildren();
	fields.forEach((field) => {
		const wrapper = document.createElement("div");
		const label = document.createElement("label");
		label.htmlFor = `field-${field.name}`;
		label.textContent = field.label;
		wrapper.append(label);

		let control;
		if (field.type === "select") {
			control = document.createElement("select");
			field.options.forEach(([value, text]) => {
				const option = document.createElement("option");
				option.value = value;
				option.textContent = text;
				control.append(option);
			});
		} else if (field.type === "textarea") {
			control = document.createElement("textarea");
			control.placeholder = field.placeholder;
			control.required = field.required;
		} else {
			control = document.createElement("input");
			control.type = "text";
			control.placeholder = field.placeholder;
			control.required = field.required;
		}

		control.id = `field-${field.name}`;
		control.name = field.name;
		if (field.minLength) control.minLength = field.minLength;
		wrapper.append(control);
		fieldsContainer.append(wrapper);
	});
}

function setMode(mode) {
	formDrafts[activeMode] = Object.fromEntries(new FormData(form).entries());
	activeMode = mode;
	const tool = tools[mode];
	document.querySelectorAll(".tool-tab").forEach((tab) => {
		tab.setAttribute("aria-selected", String(tab.dataset.mode === mode));
	});
	document.querySelector("#form-title").textContent = tool.title;
	document.querySelector("#form-description").textContent = tool.description;
	submitLabel.textContent = tool.action;
	renderFields(tool.fields);
	Object.entries(formDrafts[mode] || {}).forEach(([name, value]) => {
		const control = form.elements.namedItem(name);
		if (control) control.value = value;
	});
}

function showText(text) {
	const answer = document.createElement("div");
	answer.className = "answer-copy";
	answer.textContent = text;
	resultContent.replaceChildren(answer);
	latestResult = text;
	copyButton.hidden = !text;
}

function showQuiz(quiz) {
	const questions = Array.isArray(quiz) ? quiz : quiz.questions;
	if (!Array.isArray(questions)) {
		showText(JSON.stringify(quiz, null, 2));
		return;
	}

	const answersRevealed = new Array(questions.length).fill(false);
	function updateCopyText() {
		latestResult = questions.map((item, index) => {
			const choices = (item.options || []).join("\n");
			const answer = answersRevealed[index] ? `\nAnswer: ${item.answer}${item.explanation ? `\n${item.explanation}` : ""}` : "";
			return `${index + 1}. ${item.question}\n${choices}${answer}`;
		}).join("\n\n");
		copyButton.hidden = !latestResult;
	}

	const fragment = document.createDocumentFragment();
	questions.forEach((item, index) => {
		const article = document.createElement("article");
		article.className = "quiz-item";
		const heading = document.createElement("h3");
		heading.textContent = `${index + 1}. ${item.question}`;
		article.append(heading);
		const options = document.createElement("ul");
		options.className = "quiz-options";
		(item.options || []).forEach((option, optionIndex) => {
			const choice = document.createElement("li");
			const label = document.createElement("label");
			label.className = "quiz-choice";
			const input = document.createElement("input");
			input.type = "radio";
			input.name = `quiz-question-${index}`;
			input.value = String(optionIndex);
			label.append(input, document.createTextNode(option));
			choice.append(label);
			options.append(choice);
		});
		article.append(options);

		const feedback = document.createElement("p");
		feedback.className = "quiz-feedback";
		feedback.setAttribute("role", "status");
		feedback.setAttribute("aria-live", "polite");
		feedback.hidden = true;

		options.addEventListener("change", () => {
			const selected = options.querySelector("input:checked");
			if (!selected) return;

			const selectedAnswer = String(item.options[Number(selected.value)] || "").trim();
			const correctAnswer = String(item.answer || "").trim();
			const isCorrect = selectedAnswer.toLocaleLowerCase() === correctAnswer.toLocaleLowerCase();
			feedback.classList.add(isCorrect ? "is-correct" : "is-incorrect");
			feedback.textContent = `${isCorrect ? "Correct!" : `Not quite. The correct answer is ${correctAnswer}.`}${item.explanation ? ` ${item.explanation}` : ""}`;
			feedback.hidden = false;
			options.querySelectorAll("input").forEach((input) => { input.disabled = true; });
			answersRevealed[index] = true;
			updateCopyText();
		});

		article.append(feedback);
		fragment.append(article);
	});
	resultContent.replaceChildren(fragment);
	updateCopyText();
}

function showError(message) {
	const error = document.createElement("div");
	error.className = "error-message";
	error.textContent = message;
	resultContent.replaceChildren(error);
	latestResult = "";
	copyButton.hidden = true;
}

function getErrorMessage(data) {
	if (typeof data.error === "string") return data.error;
	if (typeof data.detail === "string") return data.detail;
	if (Array.isArray(data.detail)) {
		return data.detail
			.map((item) => item.loc?.at(-1) ? `${item.loc.at(-1)}: ${item.msg}` : item.msg)
			.filter(Boolean)
			.join("\n");
	}
	return "The request could not be completed.";
}

document.querySelectorAll(".tool-tab").forEach((tab) => {
	tab.addEventListener("click", () => setMode(tab.dataset.mode));
});

form.addEventListener("submit", async (event) => {
	event.preventDefault();
	const tool = tools[activeMode];
	const payload = Object.fromEntries(new FormData(form).entries());
	if (payload.question_count) payload.question_count = Number(payload.question_count);
	if (payload.duration) payload.duration = Number(payload.duration);

	submitButton.disabled = true;
	outputPanel.setAttribute("aria-busy", "true");
	submitLabel.textContent = "Working";
	const loading = document.createElement("div");
	loading.className = "loading-message";
	loading.innerHTML = '<span class="loading-dot" aria-hidden="true"></span><span>Putting your response together...</span>';
	resultContent.replaceChildren(loading);
	copyButton.hidden = true;

	try {
		const response = await fetch(tool.endpoint, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload)
		});
		const data = await response.json();
		if (!response.ok) throw new Error(getErrorMessage(data));
		if (activeMode === "quiz") showQuiz(data.quiz);
		else showText(data.result || "No response was returned.");
	} catch (error) {
		showError(error.message || "Could not connect to EduGenie. Check your connection and try again.");
	} finally {
		submitButton.disabled = false;
		submitLabel.textContent = tool.action;
		outputPanel.setAttribute("aria-busy", "false");
	}
});

document.querySelector("#clear-button").addEventListener("click", () => {
	const empty = document.createElement("div");
	empty.className = "empty-state";
	empty.innerHTML = '<span class="empty-mark" aria-hidden="true">?</span><strong>Your study space is ready</strong><span>Choose a tool, add a prompt, and your response will appear here.</span>';
	resultContent.replaceChildren(empty);
	latestResult = "";
	copyButton.hidden = true;
});

copyButton.addEventListener("click", async () => {
	if (!latestResult) return;
	try {
		await navigator.clipboard.writeText(latestResult);
		copyButton.textContent = "Copied";
		window.setTimeout(() => { copyButton.textContent = "Copy"; }, 1500);
	} catch {
		copyButton.textContent = "Copy unavailable";
	}
});

async function loadHealth() {
	const status = document.querySelector("#health-status");
	const label = document.querySelector("#health-label");
	try {
		const response = await fetch("/health");
		const data = await response.json();
		status.dataset.ready = String(data.gemini_configured);
		label.textContent = data.gemini_configured ? "AI ready" : "AI key needed";
	} catch {
		status.dataset.ready = "false";
		label.textContent = "Service unavailable";
	}
}

setMode(activeMode);
loadHealth();
