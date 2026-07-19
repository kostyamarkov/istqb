import Foundation

struct ExamData: Decodable {
    let examId: String
    let title: String
    let questionCount: Int
    let questions: [ExamQuestion]
}

struct ExamQuestion: Decodable, Identifiable {
    let id: Int
    let text: String
    let options: [ExamOption]
    let correctOptions: [String]
    let explanation: String

    var isMultiSelect: Bool {
        correctOptions.count > 1
    }
}

struct ExamOption: Decodable, Identifiable {
    let id: String
    let text: String

    var optionTitle: String {
        "\(id.uppercased()). \(text)"
    }
}

struct TestResult {
    let correct: Int
    let incorrect: Int
    let unanswered: Int
    let total: Int
}
