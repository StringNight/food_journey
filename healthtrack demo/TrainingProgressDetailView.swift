import SwiftUI

struct TrainingProgressDetailView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("训练进度")
                    .font(.title)
                    .bold()
                
                // 今日训练详情
                VStack(alignment: .leading, spacing: 8) {
                    Text("今日训练")
                        .font(.headline)
                    Text("深蹲: 3组 x 10次, 重量 60kg")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 训练完成度
                VStack(alignment: .leading, spacing: 8) {
                    Text("训练完成度")
                        .font(.headline)
                    ProgressView(value: 0.6, total: 1.0)
                        .progressViewStyle(LinearProgressViewStyle(tint: .green))
                        .padding(.vertical)
                    Text("完成3/5组")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 肌肉群分析
                VStack(alignment: .leading, spacing: 8) {
                    Text("肌肉群分析")
                        .font(.headline)
                    Text("今天你训练了腿部，重点锻炼了股四头肌和腿后肌。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 休息与拉伸建议
                VStack(alignment: .leading, spacing: 8) {
                    Text("休息与拉伸建议")
                        .font(.headline)
                    Text("今天进行了大肌群训练，建议休息48小时，进行腿部拉伸。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 接下来的训练计划
                VStack(alignment: .leading, spacing: 8) {
                    Text("接下来的训练")
                        .font(.headline)
                    Text("明天进行背部训练。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("训练详情")
    }
}

struct TrainingProgressDetailView_Previews: PreviewProvider {
    static var previews: some View {
        TrainingProgressDetailView()
    }
}
