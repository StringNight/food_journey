import SwiftUI

struct RecoveryDetailView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("恢复详情")
                    .font(.title)
                    .bold()
                
                // 睡眠分析
                VStack(alignment: .leading, spacing: 8) {
                    Text("睡眠分析")
                        .font(.headline)
                    Text("睡眠时长: 7小时")
                    Text("深睡: 50%")
                    Rectangle()
                        .fill(Color.blue.opacity(0.3))
                        .frame(height: 150)
                        .overlay(Text("睡眠趋势图"))
                        .cornerRadius(10)
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 疲劳感评估（星级评分）
                VStack(alignment: .leading, spacing: 8) {
                    Text("疲劳感评估")
                        .font(.headline)
                    HStack {
                        ForEach(0..<5) { index in
                            Image(systemName: index < 4 ? "star.fill" : "star")
                                .foregroundColor(.yellow)
                        }
                    }
                    Text("疲劳感: 4/5")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 恢复活动建议
                VStack(alignment: .leading, spacing: 8) {
                    Text("恢复活动建议")
                        .font(.headline)
                    Text("根据你的疲劳感，建议进行轻柔的瑜伽或拉伸。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("恢复详情")
    }
}

struct RecoveryDetailView_Previews: PreviewProvider {
    static var previews: some View {
        RecoveryDetailView()
    }
}
