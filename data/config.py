config = {
    "W": '',

    # пауза между аккаунтами в секундах
    # Pause between accounts
    "sleep_between_accs_from": 5,
    "sleep_between_accs_to": 10,

    # пауза перед следующим действиеми на одном аккунте
    # Pause between next account actions
    "sleep_between_actions_from": 5,
    "sleep_between_actions_to": 10,

    # пауза между вводом символов в процессе печатания
    # Pause between typing text (ui interaction)
    "min_typing_pause_seconds": 0.02,
    "max_typing_pause_seconds": 0.8,

    # рандом для клика на tweet
    # click deviation (ui interaction)
    "max_height_deviation_tweet_find": 0.3,
    "max_width_deviation_tweet_find": 0.3,
    
    "max_height_deviation": 0.2,
    "max_width_deviation": 0.1,

    "max_retries": 3,

    # Here you need to input the ID of the task you want to complete, you can find it on the specific task page
    # заполните ID от кампании на Galxe
    "galxe_social_tasks_ids": ['253496928496164864', '286696619215855616', '280704789634523136', '278549585866694656',
                               '301229797678948352', '288972118256427008', '291412236015673344', '293632144904462336',
                               '293750053635006464', '278340090800545792'],
    "mode": "verify_on_galxe",  # complete_social_tasks, verify_on_galxe, claim_points
    "wallets_in_batch": 10, # Rellevent only for complete_social_tasks/claim_points tasks, 'verify on galxe' is sync mode right now (1 thread)

    "anti_detect_browser": 'Dolphin'  # AdsPower,Dolphin
}
