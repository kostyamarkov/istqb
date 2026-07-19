import SwiftUI

struct StartView: View {
    var onStart: () -> Void

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Text("ISTQB Preparation")
                .font(.title)
                .fontWeight(.semibold)
                .foregroundStyle(.black)

            Text("Simple practice tests")
                .font(.subheadline)
                .foregroundStyle(.gray)

            Button(action: onStart) {
                Text("Start test")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.black)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .padding(.horizontal, 24)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.white)
    }
}
