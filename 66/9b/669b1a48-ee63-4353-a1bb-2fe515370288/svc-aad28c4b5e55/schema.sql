-- 外卖点餐后端：餐厅 / 菜品 / 订单 / 订单明细
-- 部署时执行，幂等。

CREATE TABLE IF NOT EXISTS restaurants (
    id           serial PRIMARY KEY,
    name         text NOT NULL,
    category     text NOT NULL DEFAULT '其他',
    rating       numeric(3, 2) NOT NULL DEFAULT 4.5,
    delivery_fee numeric(10, 2) NOT NULL DEFAULT 0,
    delivery_minutes integer NOT NULL DEFAULT 30,
    description  text NOT NULL DEFAULT '',
    emoji        text NOT NULL DEFAULT '🍱',
    sales        integer NOT NULL DEFAULT 0,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dishes (
    id            serial PRIMARY KEY,
    restaurant_id integer NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name          text NOT NULL,
    price         numeric(10, 2) NOT NULL,
    description   text NOT NULL DEFAULT '',
    tag           text NOT NULL DEFAULT '',
    sales         integer NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dishes_restaurant ON dishes(restaurant_id);

CREATE TABLE IF NOT EXISTS orders (
    id              serial PRIMARY KEY,
    restaurant_id   integer NOT NULL REFERENCES restaurants(id),
    restaurant_name text NOT NULL,
    customer_name   text NOT NULL DEFAULT '',
    phone           text NOT NULL DEFAULT '',
    address         text NOT NULL DEFAULT '',
    note            text NOT NULL DEFAULT '',
    total_amount    numeric(10, 2) NOT NULL DEFAULT 0,
    status          text NOT NULL DEFAULT '待商家接单',
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

CREATE TABLE IF NOT EXISTS order_items (
    id         serial PRIMARY KEY,
    order_id   integer NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    dish_id    integer,
    dish_name  text NOT NULL,
    price      numeric(10, 2) NOT NULL,
    quantity   integer NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- ============================================================
-- 初始餐厅与菜单数据（幂等 seed，部署一次后多次执行无副作用）
-- ============================================================

INSERT INTO restaurants (id, name, category, rating, delivery_fee, delivery_minutes, description, emoji, sales)
VALUES
    (1, '蜀香小炒', '川菜', 4.8, 3.0, 28, '地道川味，麻辣鲜香，每一勺都是家的味道。', '🌶️', 1820),
    (2, '粤味茶餐厅', '粤菜', 4.6, 4.0, 32, '经典广式茶餐厅，煲仔饭与丝袜奶茶是招牌。', '🍵', 1450),
    (3, '麦香汉堡', '西式快餐', 4.5, 2.0, 22, '现点现做，安格斯牛肉饼厚达 1.5cm。', '🍔', 2360),
    (4, '寿司の匠', '日料', 4.9, 6.0, 40, '空运鲜鱼，手握寿司，每一颗都是匠心。', '🍣', 980),
    (5, '兰州拉面', '面食', 4.7, 3.0, 25, '一清二白三红四绿五黄，汤底每日现熬。', '🍜', 3120),
    (6, '甜品研究所', '甜品', 4.8, 3.0, 30, '低糖手作甜品，颜值与味道都在线。', '🍰', 760),
    (7, '老北京炸酱面', '面食', 4.4, 2.5, 26, '老北京胡同味道，黄瓜丝水萝卜清爽解腻。', '🥢', 1230),
    (8, '沙县小吃', '快餐', 4.3, 1.5, 20, '国民食堂，蒸饺飘香。', '🥟', 4180)
ON CONFLICT (id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('restaurants', 'id'),
    GREATEST((SELECT COALESCE(MAX(id), 0) FROM restaurants), 1)
);

INSERT INTO dishes (id, restaurant_id, name, price, description, tag, sales)
VALUES
    -- 蜀香小炒
    (101, 1, '宫保鸡丁', 28.0, '鸡腿肉、花生米、干辣椒段，糊辣荔枝味。', '招牌', 320),
    (102, 1, '麻婆豆腐', 18.0, '嫩豆腐配郫县豆瓣，麻辣烫嫩酥香。', '热销', 410),
    (103, 1, '回锅肉', 32.0, '二刀肉先煮后炒，蒜苗豆豉提香。', '招牌', 280),
    (104, 1, '鱼香肉丝', 26.0, '咸甜酸辣四味合一，木耳笋丝清脆。', '推荐', 210),
    (105, 1, '酸辣土豆丝', 12.0, '干辣椒炝锅，酸辣开胃。', '特价', 580),
    -- 粤味茶餐厅
    (201, 2, '腊味煲仔饭', 36.0, '砂锅现焗，底部金黄锅巴酥脆。', '招牌', 260),
    (202, 2, '丝袜奶茶', 14.0, '红茶撞淡奶，茶味浓香顺滑。', '招牌', 520),
    (203, 2, '干炒牛河', 32.0, '牛肉鲜嫩，河粉爽滑不粘。', '热销', 340),
    (204, 2, '蜜汁叉烧', 38.0, '半肥瘦梅花肉，蜂蜜烤制微焦。', '推荐', 210),
    (205, 2, '菠萝油', 9.0, '酥脆菠萝包夹冰镇牛油。', '特价', 410),
    -- 麦香汉堡
    (301, 3, '经典安格斯牛肉堡', 32.0, '1.5cm 厚牛肉饼，芝士生菜番茄。', '招牌', 480),
    (302, 3, '香辣鸡腿堡', 22.0, '整块去骨鸡腿肉，香辣过瘾。', '热销', 620),
    (303, 3, '双层芝士堡', 38.0, '两层牛肉两层芝士，肉食者必选。', '推荐', 280),
    (304, 3, '黄金薯条', 12.0, '金黄酥脆，撒细海盐。', '特价', 880),
    (305, 3, '可乐（中杯）', 8.0, '冰镇加冰，畅爽解辣。', '饮料', 1020),
    -- 寿司の匠
    (401, 4, '三文鱼寿司 6 件', 48.0, '挪威空运三文鱼，现切现握。', '招牌', 180),
    (402, 4, '鳗鱼饭', 56.0, '现烤鳗鱼配秘制酱汁，米粒分明。', '招牌', 160),
    (403, 4, '北极贝刺身', 38.0, '鲜甜爽脆，蘸少许酱油即可。', '推荐', 110),
    (404, 4, '茶碗蒸', 12.0, '日式蒸蛋，入口即化。', '小食', 240),
    (405, 4, '味噌汤', 8.0, '豆味噌、海带、嫩豆腐。', '汤品', 320),
    -- 兰州拉面
    (501, 5, '牛肉拉面（大碗）', 24.0, '二细面条，牛肉四五片加萝卜。', '招牌', 680),
    (502, 5, '毛细拉面', 22.0, '细如发丝，汤汁入味更深。', '推荐', 420),
    (503, 5, '凉拌牛腱', 26.0, '牛腱肉切薄片，浇辣椒油醋汁。', '小食', 280),
    (504, 5, '卤蛋', 4.0, '老卤慢煮入味。', '加料', 540),
    (505, 5, '油泼辣子面', 18.0, '素面盖满红油辣子。', '特价', 320),
    -- 甜品研究所
    (601, 6, '杨枝甘露', 22.0, '芒果西米椰浆，港式经典。', '招牌', 260),
    (602, 6, '提拉米苏', 28.0, '意式经典，可可粉微苦回甘。', '招牌', 180),
    (603, 6, '芒果班戟', 16.0, '薄饼皮裹鲜奶油芒果丁。', '推荐', 320),
    (604, 6, '低糖巴斯克', 24.0, '减糖 30%，依旧焦香浓郁。', '热销', 140),
    -- 老北京炸酱面
    (701, 7, '老北京炸酱面', 18.0, '六必居黄酱配五花肉丁，菜码齐全。', '招牌', 480),
    (702, 7, '豆汁儿', 6.0, '地道北京风味，酸香独特。', '特色', 120),
    (703, 7, '焦圈', 5.0, '酥脆小食，配豆汁儿绝配。', '小食', 200),
    (704, 7, '酱牛肉', 32.0, '老汤酱入味，切片装盘。', '推荐', 160),
    -- 沙县小吃
    (801, 8, '招牌蒸饺（10 只）', 14.0, '皮薄馅大，鲜肉马蹄。', '招牌', 880),
    (802, 8, '飘香拌面', 10.0, '葱油拌面，咸香开胃。', '招牌', 1240),
    (803, 8, '馄饨', 10.0, '鲜肉小馄饨，汤底清鲜。', '热销', 720),
    (804, 8, '炖罐汤', 12.0, '茶树菇老鸭/排骨/乌鸡可选。', '汤品', 460),
    (805, 8, '卤鸡腿', 9.0, '秘制卤汁，咸香入骨。', '小食', 540)
ON CONFLICT (id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('dishes', 'id'),
    GREATEST((SELECT COALESCE(MAX(id), 0) FROM dishes), 1)
);