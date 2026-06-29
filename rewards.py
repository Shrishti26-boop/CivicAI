def get_badge(points):

    if points >= 500:
        return "🏆 Civic Champion"

    elif points >= 250:
        return "🥇 Gold Reporter"

    elif points >= 100:
        return "🥈 Silver Reporter"

    elif points >= 50:
        return "🥉 Bronze Reporter"

    else:
        return "🌱 Beginner"
