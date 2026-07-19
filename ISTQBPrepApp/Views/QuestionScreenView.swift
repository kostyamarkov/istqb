import SwiftUI

struct QuestionScreenView: View {
    @ObservedObject var viewModel: TestSessionViewModel
    var onFinish: (TestResult) -> Void

    var body: some View {
        let question = viewModel.currentQuestion
        let selected = viewModel.selectedOptions(for: question)
        let showEvaluation = viewModel.isQuestionRevealed(question)

        VStack(spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Progress")
                                .font(.subheadline)
                                .foregroundStyle(.black)
                            Spacer()
                            Text("Answered \(viewModel.answeredCount)/\(viewModel.exam.questions.count)")
                                .font(.caption)
                                .foregroundStyle(.gray)
                        }

                        ProgressView(value: viewModel.progress)
                            .tint(.black)
                    }

                    Text("Question \(viewModel.currentIndex + 1) of \(viewModel.exam.questions.count)")
                        .font(.subheadline)
                        .foregroundStyle(.gray)

                    Text(question.text)
                        .font(.headline)
                        .foregroundStyle(.black)

                    if question.isMultiSelect {
                        Text("Select all correct options")
                            .font(.caption)
                            .foregroundStyle(.gray)
                    }

                    ForEach(question.options) { option in
                        Button(action: {
                            viewModel.toggleSelection(optionId: option.id, for: question)
                        }) {
                            HStack(alignment: .top, spacing: 10) {
                                Text(option.id.uppercased() + ".")
                                    .fontWeight(.semibold)
                                Text(option.text)
                                    .multilineTextAlignment(.leading)
                                Spacer(minLength: 0)
                            }
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(backgroundColor(for: option.id, selected: selected, correct: Set(question.correctOptions), showEvaluation: showEvaluation))
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(borderColor(for: option.id, selected: selected, correct: Set(question.correctOptions), showEvaluation: showEvaluation), lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }
                        .buttonStyle(.plain)
                    }

                    if showEvaluation {
                        DisclosureGroup(
                            isExpanded: Binding(
                                get: { viewModel.explanationExpandedByQuestion[question.id] ?? false },
                                set: { viewModel.explanationExpandedByQuestion[question.id] = $0 }
                            ),
                            content: {
                                Text(question.explanation)
                                    .font(.subheadline)
                                    .foregroundStyle(.black)
                                    .padding(.top, 8)
                            },
                            label: {
                                Text("Explanation")
                                    .font(.headline)
                                    .foregroundStyle(.black)
                            }
                        )
                        .padding(12)
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
                .padding(16)
            }

            Divider()

            HStack(spacing: 10) {
                Button(action: { viewModel.goPrevious() }) {
                    Text("Previous")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(.systemGray5))
                        .foregroundStyle(viewModel.isFirstQuestion ? .gray : .black)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .disabled(viewModel.isFirstQuestion)

                Button(action: { viewModel.goNext() }) {
                    Text("Next")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(.systemGray5))
                        .foregroundStyle(viewModel.isLastQuestion ? .gray : .black)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .disabled(viewModel.isLastQuestion)

                Button(action: { onFinish(viewModel.result()) }) {
                    Text("Finish")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color.black)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                }
            }
            .padding(12)
            .background(Color.white)
        }
        .background(Color.white)
    }

    private func backgroundColor(for optionId: String, selected: Set<String>, correct: Set<String>, showEvaluation: Bool) -> Color {
        guard showEvaluation else {
            return selected.contains(optionId) ? Color.blue.opacity(0.12) : Color.white
        }

        if correct.contains(optionId) {
            return Color.green.opacity(0.2)
        }

        if selected.contains(optionId) {
            return Color.red.opacity(0.16)
        }

        return Color.white
    }

    private func borderColor(for optionId: String, selected: Set<String>, correct: Set<String>, showEvaluation: Bool) -> Color {
        guard showEvaluation else {
            return selected.contains(optionId) ? Color.blue : Color.gray.opacity(0.35)
        }

        if correct.contains(optionId) {
            return .green
        }

        if selected.contains(optionId) {
            return .red
        }

        return Color.gray.opacity(0.35)
    }
}
