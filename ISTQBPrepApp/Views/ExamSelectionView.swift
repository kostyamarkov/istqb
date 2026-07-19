import SwiftUI

struct ExamSelectionView: View {
    var onExamSelected: (String) -> Void

    private let examIds = ["A", "B", "C", "D"]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Choose a test")
                .font(.title2)
                .fontWeight(.semibold)
                .padding(.top, 16)

            ForEach(examIds, id: \.self) { examId in
                Button(action: { onExamSelected(examId) }) {
                    HStack {
                        Text("Test \(examId)")
                            .font(.headline)
                            .foregroundStyle(.black)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundStyle(.gray)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }

            Spacer()
        }
        .padding(.horizontal, 20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.white)
    }
}
