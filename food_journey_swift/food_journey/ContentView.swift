//
//  ContentView.swift
//  food_journey
//
//  Created by StringNight on 2024/11/30.
//

import SwiftUI

struct ChatMessage: Identifiable, Hashable {
    let id = UUID()
    let content: String
    let isSent: Bool
    let avatar: Image
    let isSending: Bool
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct ContentView: View {
    @State private var messages: [ChatMessage] = []
    @State private var inputText: String = ""
    @State private var isSending: Bool = false
    
    var body: some View {
        VStack{
            HStack {
                ZStack {
                    Circle()
                        .fill(Color.clear.shadow(.drop( radius: 6)))
                        .frame(width: 50, height: 50)
                    Image("cat") // 机器人头像
                        .resizable()
                        .aspectRatio(contentMode:.fill)
                        .frame(width: 40, height: 40)
                        .clipShape(Circle())
                        .padding(.leading, 24)
                        .padding(.trailing, 8)
                        .compositingGroup()
                        .shadow(radius: 4)
                    
                }
                VStack(alignment:.leading) {
                    Text("Food Journey") // 机器人名称
                        .font(.headline)
                        .foregroundColor(.black)
                    
                    Text("Your best cook") // 机器人描述
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
            
                
                
                Spacer()
                
                // 更多按钮
                Button(action: {
                    // 处理更多按钮的点击事件
                }) {
                    Image(systemName: "ellipsis")
                        .foregroundColor(.black)
                    
                }
                .padding(.horizontal, 24)
            }
            .padding(.vertical, -4)
            
            
            
            Divider()
                .padding(.top, 2)
                .shadow(radius: 3, y:5)
        }.background(Color.gray.opacity(0.04)).navigationBarHidden(true)
        
        VStack {
            ScrollView {
                if messages != [] {
                    ForEach(messages, id: \.self) { message in
                        HStack {
                            if message.isSent {
                                Spacer()
                                Text(message.content)
                                    .padding(.vertical, 12)
                                    .padding(.horizontal, 16)
                                    .background(Color.pink.opacity(0.75))
                                    .foregroundColor(.white)
                                    .cornerRadius(12)
                            } else {
                                if message.isSending {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint:.gray))
                                        .frame(width: 30, height: 30)
                                }
                                else {
                                    Text(message.content)
                                        .padding(.vertical, 12)
                                        .padding(.horizontal, 16)
                                        .background(Color.gray.opacity(0.1))
                                        .cornerRadius(12)
                                    Spacer()
                                }
                            }}
                    }} else {
                        Spacer()
                            .padding(.bottom, 150)
                        ZStack(alignment: .center) {
                            Image("ollama") // 机器人头像
                                .resizable()
                                .aspectRatio(contentMode:.fill)
                                .frame(width: 180, height: 180)
                                .clipShape(Circle())
                                .compositingGroup()
                            
                        }
                    }
            }
            .padding(.top, 6).padding(.horizontal, 12)
        }
        VStack {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack() {
                    // 快捷操作栏
                    Button(action: {
                        inputText = "杭椒牛柳的做法"
                        Task {
                            await sendMessage()
                        }
                    }) {
                        Image(systemName: "fork.knife").padding(.trailing, -2)
                        Text("杭椒牛柳")
                    }
                    .controlSize(.mini)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(Color.gray.opacity(0.05))
                    .foregroundColor(.black)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10).stroke(Color.gray, lineWidth: 1))
                    
                    
                    Button(action: {
                        inputText = "宫保鸡丁的做法"
                        Task {
                            await sendMessage()
                        }
                    }) {
                        Image(systemName: "fork.knife").padding(.trailing, -2)
                        Text("宫保鸡丁")
                    }
                    .controlSize(.mini)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(Color.gray.opacity(0.05))
                    .foregroundColor(.black)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10).stroke(Color.gray, lineWidth: 1))
                    
                    
                    Button(action: {
                        inputText = "鱼香肉丝的做法"
                        Task {
                            await sendMessage()
                        }
                    }) {
                        Image(systemName: "fork.knife").padding(.trailing, -2)
                        Text("鱼香肉丝")
                    }
                    .controlSize(.mini)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(Color.gray.opacity(0.05))
                    .foregroundColor(.black)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10).stroke(Color.gray, lineWidth: 1))
                    
                    
                    Button(action: {
                        inputText = "我想了解更多产品信息。"
                        Task {
                            await sendMessage()
                        }
                    }) {
                        Image(systemName: "book.fill").padding(.trailing, -2)
                        Text("产品信息")
                        
                    }
                    .controlSize(.mini)            .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(Color.gray.opacity(0.05))
                    .foregroundColor(.black)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10).stroke(Color.gray, lineWidth: 1))
                    
                    Spacer()
                    
                }.padding(.horizontal, 12).padding(.vertical, 3)
            }
            
            HStack {
                TextField("输入消息...", text: $inputText)
                    .padding(.vertical, 10)
                    .padding(.leading, 12)
                    .background(Color.white.opacity(1))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10).stroke(Color.black, lineWidth: 0.5))
                
                
                Button(action: {
                    if inputText != "" {
                        Task {
                            await sendMessage()
                        }
                        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                    }
                    
                }) {
                    Image(systemName: "paperplane")
                        .padding(.vertical, 11)
                        .padding(.horizontal, 13)
                        .background(Color.pink.opacity(0.8))
                        .foregroundColor(.white)
                        .cornerRadius(10)
                        .shadow(radius: 2)
                }
            }
            .padding(.bottom, 16)
            .padding(.horizontal, 12)
            .shadow(radius: 3.5)
        }.background(Color.gray.opacity(0.03))
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("完成") {
                        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                    }.padding(.horizontal, -4)
                }
            }
        
    }
    
    
    private func sendMessage() async {
        let userMessage = ChatMessage(
            content: inputText,
            isSent: true,
            avatar: Image(systemName: "person.circle"),
            isSending: false
        )
        messages.append(userMessage)
        
        let userInput = inputText
        inputText = ""  // 清空输入框
        
        // 添加等待消息
        let progressMessage = ChatMessage(
            content: "",
            isSent: false,
            avatar: Image(systemName: "clock"),
            isSending: true
        )
        messages.append(progressMessage)
        
        do {
            // 移除等待消息
            messages.removeLast()
            
            // 发送消息并获取响应
            let response = try await NetworkService.shared.sendChatMessage(userInput)
            
            // 添加机器人回复
            let botMessage = ChatMessage(
                content: response.message,
                isSent: false,
                avatar: Image(systemName: "brain"),
                isSending: false
            )
            messages.append(botMessage)
            
            // 如果有建议，添加建议消息
            if let suggestions = response.suggestions {
                for suggestion in suggestions {
                    let suggestionMessage = ChatMessage(
                        content: suggestion,
                        isSent: false,
                        avatar: Image(systemName: "lightbulb"),
                        isSending: false
                    )
                    messages.append(suggestionMessage)
                }
            }
        } catch {
            // 移除等待消息
            messages.removeLast()
            
            // 添加错误消息
            let errorMessage = ChatMessage(
                content: "发送失败: \(error.localizedDescription)",
                isSent: false,
                avatar: Image(systemName: "exclamationmark.triangle"),
                isSending: false
            )
            messages.append(errorMessage)
        }
    }
}

#Preview {
    ContentView()
}
