import SwiftUI

struct ChatRow: View {


    var body: some View {
        HStack {
            Image("cat")
                .resizable()
                .frame(width: 50, height: 50)
            Text("Chat Example")
            Spacer()
        }
    }
}
