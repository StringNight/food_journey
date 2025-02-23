import SwiftUI
import Charts

struct BodyDataDetailView: View {
    
    // 模拟数据
    let weightData: [WeightEntry] = [
        WeightEntry(day: "周一", weight: 72),
        WeightEntry(day: "周二", weight: 71.8),
        WeightEntry(day: "周三", weight: 72.2),
        WeightEntry(day: "周四", weight: 72),
        WeightEntry(day: "周五", weight: 71.9),
        WeightEntry(day: "周六", weight: 72.1),
        WeightEntry(day: "周日", weight: 72)
    ]
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("身体数据")
                    .font(.title)
                    .bold()
                
                // 基本指标
                HStack {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("体重: 72kg")
                        Text("体脂率: 20%")
                        Text("肌肉量: 35kg")
                        Text("基础代谢率 (BMR): 1800 kcal")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                    }
                    Spacer()
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 图表展示
                Text("体重变化趋势（过去一周）")
                    .font(.headline)
                Chart {
                    ForEach(weightData) { entry in
                        LineMark(
                            x: .value("日期", entry.day),
                            y: .value("体重", entry.weight)
                        )
                    }
                }
                .frame(height: 200)
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 分析与建议
                Text("分析与建议")
                    .font(.headline)
                Text("你的体脂率正在减少，但体重保持稳定。继续保持现有训练强度，增加肌肉量。")
                    .padding()
                    .background(Color(UIColor.secondarySystemBackground))
                    .cornerRadius(10)
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("身体数据详情")
    }
}

struct WeightEntry: Identifiable {
    var id = UUID()
    var day: String
    var weight: Double
}

struct BodyDataDetailView_Previews: PreviewProvider {
    static var previews: some View {
        BodyDataDetailView()
    }
}
