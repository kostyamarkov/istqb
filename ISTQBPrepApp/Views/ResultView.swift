import SwiftUI

struct ResultView: View {
    let result: TestResult
    let onBackToHome: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            Text("Test completed")
                .font(.title2)
                .fontWeight(.semibold)

            summaryRow(title: "Correct", value: result.correct, color: .green)
            summaryRow(title: "Incorrect", value: result.incorrect, color: .red)
            summaryRow(title: "Unanswered", value: result.unanswered, color: .gray)

            Text("Total: \(result.total)")
                .font(.headline)
                .padding(.top, 8)

            Button(action: onBackToHome) {
                Text("Back to Home")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.black)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .padding(.horizontal, 24)
            .padding(.top, 12)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.white)
    }

    private func summaryRow(title: String, value: Int, color: Color) -> some View {
        HStack {
            Text(title)
                .foregroundStyle(.black)
            Spacer()
            Text("\(value)")
                .foregroundStyle(color)
                .fontWeight(.semibold)
        }
        .padding(.horizontal, 24)
    }
}
