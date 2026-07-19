import SwiftUI
import UIKit

@main
struct ISTQBPrepApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            AppRootView()
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, supportedInterfaceOrientationsFor window: UIWindow?) -> UIInterfaceOrientationMask {
        .portrait
    }
}

struct AppRootView: View {
    private enum Screen {
        case start
        case selection
        case test(TestSessionViewModel)
        case result(TestResult)
    }

    @State private var screen: Screen = .start
    private let repository = ExamRepository()

    var body: some View {
        Group {
            switch screen {
            case .start:
                StartView {
                    screen = .selection
                }

            case .selection:
                ExamSelectionView { examId in
                    loadExamAndStart(examId: examId)
                }

            case .test(let viewModel):
                QuestionScreenView(viewModel: viewModel) { result in
                    screen = .result(result)
                }

            case .result(let result):
                ResultView(result: result) {
                    screen = .start
                }
            }
        }
        .background(Color.white)
    }

    private func loadExamAndStart(examId: String) {
        do {
            let exam = try repository.loadExam(examId: examId)
            let vm = TestSessionViewModel(exam: exam)
            screen = .test(vm)
        } catch {
            screen = .start
        }
    }
}
