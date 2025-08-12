import random


class Lottery:
    def __init__(self, name, rewards):
        self.name = name
        self.rewards = rewards
        self.top_tier_guarantee_counter = 0  # 记录抽奖次数以实现第一档保底机制
        self.ten_draw_guarantee_counter = 0  # 记录十连抽奖次数以实现第二档保底机制

    def draw(self, draw_count):
        results = []
        first_tier_rewarded = False

        for i in range(draw_count):
            reward = self.perform_draw()

            # 如果这是一次十连抽的第一个抽奖，重置保底标志
            if i % 10 == 0:
                first_tier_rewarded = False

            # 每次十连抽保证第二档及以上奖励
            if (i + 1) % 10 == 0 and not any(probability <= 0.2 for item, probability in results[-9:]):
                # 如果前9次抽奖中没有第二档及以上奖励，替换最后一次抽奖的结果
                reward = self.guaranteed_draw(min_probability=0.2)

            # 检查第一档奖励保底
            if reward['probability'] <= 0.03:
                self.top_tier_guarantee_counter = 0  # 重置保底计数器
                first_tier_rewarded = True
            else:
                self.top_tier_guarantee_counter += 1  # 增加保底计数器

            # 处理第一档奖励保底机制
            if self.top_tier_guarantee_counter >= 100:
                reward = self.guaranteed_draw(min_probability=0.03)
                self.top_tier_guarantee_counter = 0

            # 存储奖励和概率
            results.append((reward['item'], reward['probability']))

        return results

    def perform_draw(self):
        roll = random.random()
        cumulative_probability = 0.0

        for reward in self.rewards:
            cumulative_probability += reward['probability']
            if roll <= cumulative_probability:
                return reward

        return self.rewards[-1]  # 默认返回最后一项，防止概率问题

    def guaranteed_draw(self, min_probability):
        """返回满足最小概率条件的奖励"""
        eligible_rewards = [r for r in self.rewards if r['probability'] <= min_probability]
        return random.choice(eligible_rewards) if eligible_rewards else self.rewards[0]
