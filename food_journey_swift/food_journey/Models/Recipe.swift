import Foundation

public struct Recipe: Codable, Identifiable {
    public let id: String
    public let title: String
    public let ingredients: [Ingredient]
    public let steps: [Step]
    public let nutrition: Nutrition
    public let cookingTime: Int?
    public let difficulty: String?
    public let tags: [String]?
    public let createdAt: Date
    public let authorId: String
    public let imageUrl: String?
    
    enum CodingKeys: String, CodingKey {
        case id, title, ingredients, steps, nutrition, tags
        case cookingTime = "cooking_time"
        case difficulty
        case createdAt = "created_at"
        case authorId = "author_id"
        case imageUrl = "image_url"
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        ingredients = try container.decode([Ingredient].self, forKey: .ingredients)
        steps = try container.decode([Step].self, forKey: .steps)
        nutrition = try container.decode(Nutrition.self, forKey: .nutrition)
        cookingTime = try container.decodeIfPresent(Int.self, forKey: .cookingTime)
        difficulty = try container.decodeIfPresent(String.self, forKey: .difficulty)
        tags = try container.decodeIfPresent([String].self, forKey: .tags)
        imageUrl = try container.decodeIfPresent(String.self, forKey: .imageUrl)
        authorId = try container.decode(String.self, forKey: .authorId)
        
        let dateString = try container.decode(String.self, forKey: .createdAt)
        if let date = ISO8601DateFormatter().date(from: dateString) {
            createdAt = date
        } else {
            throw DecodingError.dataCorruptedError(forKey: .createdAt, in: container, debugDescription: "Date string does not match expected format")
        }
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(title, forKey: .title)
        try container.encode(ingredients, forKey: .ingredients)
        try container.encode(steps, forKey: .steps)
        try container.encode(nutrition, forKey: .nutrition)
        try container.encodeIfPresent(cookingTime, forKey: .cookingTime)
        try container.encodeIfPresent(difficulty, forKey: .difficulty)
        try container.encodeIfPresent(tags, forKey: .tags)
        try container.encodeIfPresent(imageUrl, forKey: .imageUrl)
        try container.encode(authorId, forKey: .authorId)
        
        let dateString = ISO8601DateFormatter().string(from: createdAt)
        try container.encode(dateString, forKey: .createdAt)
    }
}

public struct Ingredient: Codable {
    public let name: String
    public let amount: String
    public let unit: String?
    
    public init(name: String, amount: String, unit: String?) {
        self.name = name
        self.amount = amount
        self.unit = unit
    }
}

public struct Step: Codable {
    public let stepNumber: Int
    public let description: String
    public let image: String?
    public let tips: String?
    
    enum CodingKeys: String, CodingKey {
        case stepNumber = "step_number"
        case description, image, tips
    }
    
    public init(stepNumber: Int, description: String, image: String?, tips: String?) {
        self.stepNumber = stepNumber
        self.description = description
        self.image = image
        self.tips = tips
    }
}

public struct Nutrition: Codable {
    public let calories: Float
    public let protein: Float
    public let carbs: Float
    public let fat: Float
    public let fiber: Float?
    public let vitamins: [String: Float]?
    
    public init(calories: Float, protein: Float, carbs: Float, fat: Float, fiber: Float?, vitamins: [String: Float]?) {
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.fiber = fiber
        self.vitamins = vitamins
    }
} 
