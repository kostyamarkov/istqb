import Foundation

final class ExamRepository {
    func loadExam(examId: String) throws -> ExamData {
        let fileName = "exam_\(examId)"
        guard let url = Bundle.main.url(forResource: fileName, withExtension: "json") else {
            throw NSError(domain: "ExamRepository", code: 404, userInfo: [NSLocalizedDescriptionKey: "Missing file \(fileName).json in app bundle"])
        }

        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(ExamData.self, from: data)
    }
}
