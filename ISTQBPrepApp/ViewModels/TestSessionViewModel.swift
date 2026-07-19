import Foundation

@MainActor
final class TestSessionViewModel: ObservableObject {
    @Published private(set) var exam: ExamData
    @Published var currentIndex: Int = 0
    @Published private(set) var selectedByQuestion: [Int: Set<String>] = [:]
    @Published private(set) var revealedQuestions: Set<Int> = []
    @Published var explanationExpandedByQuestion: [Int: Bool] = [:]

    init(exam: ExamData) {
        self.exam = exam
    }

    var currentQuestion: ExamQuestion {
        exam.questions[currentIndex]
    }

    var isFirstQuestion: Bool {
        currentIndex == 0
    }

    var isLastQuestion: Bool {
        currentIndex == exam.questions.count - 1
    }

    var answeredCount: Int {
        exam.questions.reduce(into: 0) { result, question in
            let selected = selectedByQuestion[question.id] ?? []
            if !selected.isEmpty {
                result += 1
            }
        }
    }

    var progress: Double {
        guard exam.questions.count > 0 else { return 0 }
        return Double(answeredCount) / Double(exam.questions.count)
    }

    func selectedOptions(for question: ExamQuestion) -> Set<String> {
        selectedByQuestion[question.id] ?? []
    }

    func isQuestionRevealed(_ question: ExamQuestion) -> Bool {
        revealedQuestions.contains(question.id)
    }

    func toggleSelection(optionId: String, for question: ExamQuestion) {
        var selected = selectedByQuestion[question.id] ?? []

        if question.isMultiSelect {
            if selected.contains(optionId) {
                selected.remove(optionId)
            } else {
                selected.insert(optionId)
            }
        } else {
            selected = [optionId]
        }

        selectedByQuestion[question.id] = selected
        revealedQuestions.insert(question.id)

        if explanationExpandedByQuestion[question.id] == nil {
            explanationExpandedByQuestion[question.id] = false
        }
    }

    func goNext() {
        guard currentIndex < exam.questions.count - 1 else { return }
        currentIndex += 1
    }

    func goPrevious() {
        guard currentIndex > 0 else { return }
        currentIndex -= 1
    }

    func result() -> TestResult {
        var correct = 0
        var incorrect = 0
        var unanswered = 0

        for question in exam.questions {
            let selected = selectedByQuestion[question.id] ?? []
            if selected.isEmpty {
                unanswered += 1
                continue
            }

            let expected = Set(question.correctOptions)
            if selected == expected {
                correct += 1
            } else {
                incorrect += 1
            }
        }

        return TestResult(correct: correct, incorrect: incorrect, unanswered: unanswered, total: exam.questions.count)
    }
}
