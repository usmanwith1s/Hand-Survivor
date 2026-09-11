import cv2
import mediapipe as mp
import time
import random
import math


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="hand_landmarker.task"
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1
)


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

window_name = "Hand Game"

cv2.namedWindow(
    window_name,
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    window_name,
    800,
    600
)

if not cap.isOpened():
    print("Could not access camera.")
    exit()


# ============================================================
# SCREEN
# ============================================================

WIDTH = 640
HEIGHT = 480


# ============================================================
# PLAYER
# ============================================================

player_x = WIDTH // 2
player_y = 400
player_size = 50


# ============================================================
# TRACKING MEMORY
# ============================================================

last_target_x = player_x
last_target_y = player_y

velocity_x = 0
velocity_y = 0

lost_frames = 0
max_lost_frames = 8


# ============================================================
# LIVES
# ============================================================

MAX_LIVES = 3
lives = MAX_LIVES

hit_invincible = False
hit_invincible_until = 0

HIT_INVINCIBILITY = 1.2


# ============================================================
# SUPERPOWER
# ============================================================

super_power_ready = True
super_power_active = False

super_power_until = 0
super_power_cooldown_until = 0

SUPER_POWER_DURATION = 3.0
SUPER_POWER_COOLDOWN = 8.0

last_fist_state = False


# ============================================================
# PAUSE
# ============================================================

paused = False
last_open_hand_state = False


# ============================================================
# GAME STATE
# ============================================================

game_started = False
game_over = False


# ============================================================
# SCORE / COMBO
# ============================================================

score = 0
high_score = 0

combo = 0
best_combo = 0


# ============================================================
# WAVES
# ============================================================

wave = 1

wave_message = ""
wave_message_until = 0

WAVE_LENGTH = 15


# ============================================================
# OBSTACLES
# ============================================================

obstacles = []

OBSTACLE_SIZE = 45

spawn_timer = 0


# ============================================================
# POWER UPS
# ============================================================

powerups = []

powerup_timer = 0

POWERUP_INTERVAL = 350


# ============================================================
# MEDIAPIPE TIMESTAMP
# ============================================================

# IMPORTANT:
# This timestamp must NEVER reset during the lifetime of
# the MediaPipe VIDEO landmarker.
#
# The old version reset start_time when R was pressed.
# That caused:
#
# ValueError: Input timestamp must be monotonically increasing.
#
# We therefore keep one permanent timestamp clock.

program_start_time = time.monotonic()


# ============================================================
# GAME TIMER
# ============================================================

game_start_time = time.monotonic()


# ============================================================
# OBSTACLE CREATION
# ============================================================

def create_obstacle():

    obstacle_types = ["normal"]

    if score >= 8:
        obstacle_types.append("fast")

    if score >= 15:
        obstacle_types.append("heavy")

    if score >= 25:
        obstacle_types.append("zigzag")

    if score >= 40:
        obstacle_types.append("danger")


    obstacle_type = random.choice(obstacle_types)


    if obstacle_type == "normal":

        size = 45
        speed_multiplier = 1.0

    elif obstacle_type == "fast":

        size = 32
        speed_multiplier = 1.8

    elif obstacle_type == "heavy":

        size = 65
        speed_multiplier = 0.65

    elif obstacle_type == "zigzag":

        size = 42
        speed_multiplier = 1.0

    else:

        size = 38
        speed_multiplier = 1.25


    return {
        "x": random.randint(
            size,
            WIDTH - size
        ),

        "y": -size,

        "size": size,

        "type": obstacle_type,

        "speed": speed_multiplier,

        "phase": random.uniform(
            0,
            math.pi * 2
        ),

        "amplitude": random.randint(
            30,
            90
        ),

        "passed": False
    }


# ============================================================
# POWERUP CREATION
# ============================================================

def create_powerup():

    return {
        "x": random.randint(
            30,
            WIDTH - 30
        ),

        "y": -30,

        "size": 24,

        "speed": 3.5
    }


# ============================================================
# RESET GAME
# ============================================================

def reset_game():

    global player_x
    global player_y

    global last_target_x
    global last_target_y

    global velocity_x
    global velocity_y

    global lost_frames

    global lives

    global hit_invincible
    global hit_invincible_until

    global super_power_ready
    global super_power_active
    global super_power_until
    global super_power_cooldown_until

    global last_fist_state
    global last_open_hand_state

    global score
    global combo
    global best_combo

    global wave
    global wave_message
    global wave_message_until

    global obstacles
    global spawn_timer

    global powerups
    global powerup_timer

    global game_over
    global paused

    global game_start_time


    player_x = WIDTH // 2
    player_y = 400

    last_target_x = player_x
    last_target_y = player_y

    velocity_x = 0
    velocity_y = 0

    lost_frames = 0


    lives = MAX_LIVES

    hit_invincible = False
    hit_invincible_until = 0


    super_power_ready = True
    super_power_active = False

    super_power_until = 0
    super_power_cooldown_until = 0


    last_fist_state = False
    last_open_hand_state = False


    score = 0
    combo = 0
    best_combo = 0


    wave = 1

    wave_message = "WAVE 1"

    wave_message_until = (
        time.monotonic() + 2
    )


    obstacles = []

    for i in range(3):

        obstacle = create_obstacle()

        obstacle["y"] = random.randint(
            -450,
            -50
        )

        obstacles.append(
            obstacle
        )


    spawn_timer = 0


    powerups = []

    powerup_timer = 0


    game_over = False
    paused = False


    game_start_time = time.monotonic()


# ============================================================
# START GAME
# ============================================================

def start_game():

    global game_started

    game_started = True

    reset_game()


# ============================================================
# GESTURE FUNCTIONS
# ============================================================

def angle(a, b, c):

    ba_x = a.x - b.x
    ba_y = a.y - b.y

    bc_x = c.x - b.x
    bc_y = c.y - b.y

    dot = (
        ba_x * bc_x +
        ba_y * bc_y
    )

    mag_ba = math.sqrt(
        ba_x ** 2 +
        ba_y ** 2
    )

    mag_bc = math.sqrt(
        bc_x ** 2 +
        bc_y ** 2
    )

    if mag_ba == 0 or mag_bc == 0:
        return 0

    cosine = dot / (
        mag_ba * mag_bc
    )

    cosine = max(
        -1,
        min(1, cosine)
    )

    return math.degrees(
        math.acos(cosine)
    )


def finger_extended(
    hand,
    mcp,
    pip,
    dip,
    tip
):

    first = angle(
        hand[mcp],
        hand[pip],
        hand[dip]
    )

    second = angle(
        hand[pip],
        hand[dip],
        hand[tip]
    )

    return (
        first > 145
        and
        second > 145
    )


def detect_gestures(hand):

    thumb = (
        angle(
            hand[1],
            hand[2],
            hand[3]
        ) > 145
        and
        angle(
            hand[2],
            hand[3],
            hand[4]
        ) > 145
    )


    index = finger_extended(
        hand,
        5,
        6,
        7,
        8
    )


    middle = finger_extended(
        hand,
        9,
        10,
        11,
        12
    )


    ring = finger_extended(
        hand,
        13,
        14,
        15,
        16
    )


    pinky = finger_extended(
        hand,
        17,
        18,
        19,
        20
    )


    open_hand = (
        thumb
        and
        index
        and
        middle
        and
        ring
        and
        pinky
    )


    fist = not (
        thumb
        or
        index
        or
        middle
        or
        ring
        or
        pinky
    )


    return open_hand, fist


# ============================================================
# INITIAL GAME STATE
# ============================================================

reset_game()

game_started = False


# ============================================================
# MEDIAPIPE
# ============================================================

with HandLandmarker.create_from_options(options) as landmarker:

    while True:

        # ====================================================
        # CAMERA
        # ====================================================

        success, frame = cap.read()

        if not success:

            print("Could not read camera.")
            break


        frame = cv2.flip(
            frame,
            1
        )


        # ====================================================
        # MEDIAPIPE IMAGE
        # ====================================================

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )


        # ====================================================
        # MONOTONIC MEDIAPIPE TIMESTAMP
        # ====================================================

        timestamp = int(
            (
                time.monotonic()
                -
                program_start_time
            )
            *
            1000
        )


        result = landmarker.detect_for_video(
            mp_image,
            timestamp
        )


        current_time = time.monotonic()


        # ====================================================
        # GESTURE STATE
        # ====================================================

        open_hand_detected = False
        fist_detected = False


        if result.hand_landmarks:

            hand = result.hand_landmarks[0]


            open_hand_detected, fist_detected = (
                detect_gestures(hand)
            )


            # =================================================
            # PLAYER CONTROL
            # =================================================

            if (
                game_started
                and
                not game_over
                and
                not paused
            ):

                index_tip = hand[8]


                target_x = int(
                    index_tip.x *
                    frame.shape[1]
                )


                target_y = int(
                    index_tip.y *
                    frame.shape[0]
                )


                movement_x = (
                    target_x -
                    last_target_x
                )


                movement_y = (
                    target_y -
                    last_target_y
                )


                velocity_x = movement_x
                velocity_y = movement_y


                last_target_x = target_x
                last_target_y = target_y


                player_x += int(
                    (
                        target_x -
                        player_x
                    )
                    *
                    0.45
                )


                player_y += int(
                    (
                        target_y -
                        player_y
                    )
                    *
                    0.45
                )


                lost_frames = 0


        # ====================================================
        # TRACKING LOSS
        # ====================================================

        if (
            not result.hand_landmarks
            and
            game_started
            and
            not game_over
            and
            not paused
        ):

            lost_frames += 1


            if lost_frames <= max_lost_frames:

                player_x += velocity_x
                player_y += velocity_y

            else:

                velocity_x = 0
                velocity_y = 0


        # ====================================================
        # START GESTURE
        # ====================================================

        if (
            not game_started
            and
            fist_detected
            and
            not last_fist_state
        ):

            start_game()


        # ====================================================
        # PAUSE GESTURE
        # ====================================================

        if (
            game_started
            and
            open_hand_detected
            and
            not last_open_hand_state
            and
            not game_over
        ):

            paused = not paused


        last_open_hand_state = (
            open_hand_detected
        )


        # ====================================================
        # SUPERPOWER GESTURE
        # ====================================================

        if (
            game_started
            and
            fist_detected
            and
            not last_fist_state
            and
            not paused
            and
            not game_over
            and
            super_power_ready
        ):

            super_power_active = True

            super_power_ready = False


            super_power_until = (
                current_time +
                SUPER_POWER_DURATION
            )


            super_power_cooldown_until = (
                current_time +
                SUPER_POWER_DURATION +
                SUPER_POWER_COOLDOWN
            )


            # Destroy all current obstacles

            obstacles.clear()


        last_fist_state = fist_detected


        # ====================================================
        # SUPERPOWER TIMER
        # ====================================================

        if super_power_active:

            if current_time >= super_power_until:

                super_power_active = False


        # ====================================================
        # SUPERPOWER RECHARGE
        # ====================================================

        if not super_power_ready:

            if (
                not super_power_active
                and
                current_time >=
                super_power_cooldown_until
            ):

                super_power_ready = True


        # ====================================================
        # GAME UPDATE
        # ====================================================

        if (
            game_started
            and
            not game_over
            and
            not paused
        ):


            # =================================================
            # WAVE
            # =================================================

            new_wave = (
                score //
                WAVE_LENGTH
            ) + 1


            if new_wave > wave:

                wave = new_wave

                wave_message = (
                    f"WAVE {wave}"
                )


                wave_message_until = (
                    current_time + 2
                )


            # =================================================
            # DIFFICULTY
            # =================================================

            obstacle_speed = min(
                18,
                5 +
                score * 0.20
            )


            spawn_interval = max(
                16,
                48 -
                int(
                    score *
                    0.35
                )
            )


            # =================================================
            # SPAWN OBSTACLES
            # =================================================

            spawn_timer += 1


            if spawn_timer >= spawn_interval:

                spawn_timer = 0

                spawn_count = 1


                if score >= 20:

                    if random.random() < 0.25:

                        spawn_count = 2


                if score >= 40:

                    if random.random() < 0.35:

                        spawn_count = 2


                if score >= 70:

                    if random.random() < 0.20:

                        spawn_count = 3


                for i in range(spawn_count):

                    obstacles.append(
                        create_obstacle()
                    )


            # =================================================
            # MOVE OBSTACLES
            # =================================================

            for obstacle in obstacles:

                obstacle["y"] += (
                    obstacle_speed *
                    obstacle["speed"]
                )


                # Zigzag movement

                if (
                    obstacle["type"]
                    ==
                    "zigzag"
                ):

                    obstacle["x"] += (
                        math.sin(
                            obstacle["y"]
                            *
                            0.035
                            +
                            obstacle["phase"]
                        )
                        *
                        3
                    )


                    obstacle["x"] = max(
                        obstacle["size"],
                        min(
                            WIDTH -
                            obstacle["size"],
                            obstacle["x"]
                        )
                    )


            # =================================================
            # POWERUP SPAWN
            # =================================================

            powerup_timer += 1


            if (
                powerup_timer
                >=
                POWERUP_INTERVAL
            ):

                powerup_timer = 0

                powerups.append(
                    create_powerup()
                )


            # =================================================
            # MOVE POWERUPS
            # =================================================

            for powerup in powerups:

                powerup["y"] += (
                    powerup["speed"]
                )


        # ====================================================
        # PLAYER BOUNDARIES
        # ====================================================

        half_player = (
            player_size //
            2
        )


        player_x = max(
            half_player,
            min(
                WIDTH -
                half_player,
                player_x
            )
        )


        player_y = max(
            half_player,
            min(
                HEIGHT -
                half_player,
                player_y
            )
        )


        # ====================================================
        # INVINCIBILITY
        # ====================================================

        if hit_invincible:

            if (
                current_time
                >=
                hit_invincible_until
            ):

                hit_invincible = False


        # ====================================================
        # PLAYER COLLISION BOX
        # ====================================================

        player_left = (
            player_x -
            player_size //
            2
        )


        player_right = (
            player_x +
            player_size //
            2
        )


        player_top = (
            player_y -
            player_size //
            2
        )


        player_bottom = (
            player_y +
            player_size //
            2
        )


        # ====================================================
        # OBSTACLE COLLISION
        # ====================================================

        if (
            game_started
            and
            not game_over
            and
            not paused
            and
            not super_power_active
            and
            not hit_invincible
        ):

            for obstacle in obstacles:

                size = obstacle["size"]


                left = (
                    obstacle["x"] -
                    size //
                    2
                )


                right = (
                    obstacle["x"] +
                    size //
                    2
                )


                top = (
                    obstacle["y"] -
                    size //
                    2
                )


                bottom = (
                    obstacle["y"] +
                    size //
                    2
                )


                collision = (
                    player_left < right
                    and
                    player_right > left
                    and
                    player_top < bottom
                    and
                    player_bottom > top
                )


                if collision:

                    lives -= 1

                    combo = 0

                    hit_invincible = True


                    hit_invincible_until = (
                        current_time +
                        HIT_INVINCIBILITY
                    )


                    obstacle["y"] = (
                        HEIGHT +
                        200
                    )


                    if lives <= 0:

                        game_over = True


                        if score > high_score:

                            high_score = score


                    break


        # ====================================================
        # POWERUP COLLECTION
        # ====================================================

        remaining_powerups = []


        for powerup in powerups:

            dx = (
                player_x -
                powerup["x"]
            )


            dy = (
                player_y -
                powerup["y"]
            )


            distance = math.sqrt(
                dx * dx +
                dy * dy
            )


            if distance < (
                player_size //
                2 +
                powerup["size"]
            ):

                # Instantly recharge superpower

                super_power_ready = True

                super_power_active = False

                super_power_cooldown_until = 0

                score += 3


            elif (
                powerup["y"]
                <
                HEIGHT + 50
            ):

                remaining_powerups.append(
                    powerup
                )


        powerups = remaining_powerups


        # ====================================================
        # REMOVE PASSED OBSTACLES
        # ====================================================

        remaining_obstacles = []


        for obstacle in obstacles:

            if (
                obstacle["y"]
                <=
                HEIGHT +
                obstacle["size"]
            ):

                remaining_obstacles.append(
                    obstacle
                )

            else:

                if not game_over:

                    score += 1

                    combo += 1


                    best_combo = max(
                        best_combo,
                        combo
                    )


                    if score > high_score:

                        high_score = score


        obstacles = remaining_obstacles


        # ====================================================
        # DRAW OBSTACLES
        # ====================================================

        for obstacle in obstacles:

            size = obstacle["size"]

            x = int(
                obstacle["x"]
            )

            y = int(
                obstacle["y"]
            )


            left = int(
                x -
                size //
                2
            )


            top = int(
                y -
                size //
                2
            )


            right = int(
                x +
                size //
                2
            )


            bottom = int(
                y +
                size //
                2
            )


            # =================================================
            # NORMAL
            # =================================================

            if (
                obstacle["type"]
                ==
                "normal"
            ):

                draw_color = (
                    0,
                    0,
                    255
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    draw_color,
                    -1
                )


            # =================================================
            # FAST
            # =================================================

            elif (
                obstacle["type"]
                ==
                "fast"
            ):

                draw_color = (
                    0,
                    165,
                    255
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    draw_color,
                    -1
                )


            # =================================================
            # HEAVY
            # =================================================

            elif (
                obstacle["type"]
                ==
                "heavy"
            ):

                draw_color = (
                    255,
                    0,
                    180
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    draw_color,
                    -1
                )


            # =================================================
            # ZIGZAG
            # =================================================

            elif (
                obstacle["type"]
                ==
                "zigzag"
            ):

                draw_color = (
                    0,
                    255,
                    255
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    draw_color,
                    -1
                )


                cv2.line(
                    frame,
                    (left, top),
                    (right, bottom),
                    (0, 0, 0),
                    3
                )


                cv2.line(
                    frame,
                    (right, top),
                    (left, bottom),
                    (0, 0, 0),
                    3
                )


            # =================================================
            # DANGER
            # =================================================

            else:

                draw_color = (
                    40,
                    40,
                    40
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    draw_color,
                    -1
                )


                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    (255, 255, 255),
                    2
                )


        # ====================================================
        # DRAW POWERUPS
        # ====================================================

        for powerup in powerups:

            x = int(
                powerup["x"]
            )

            y = int(
                powerup["y"]
            )

            size = powerup["size"]


            cv2.circle(
                frame,
                (x, y),
                size,
                (255, 215, 0),
                -1
            )


            cv2.putText(
                frame,
                "+",
                (
                    x - 10,
                    y + 10
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 0),
                3
            )


        # ====================================================
        # SUPERPOWER EFFECT
        # ====================================================

        if super_power_active:

            cv2.rectangle(
                frame,
                (0, 0),
                (
                    WIDTH - 1,
                    HEIGHT - 1
                ),
                (0, 255, 255),
                7
            )


            cv2.putText(
                frame,
                "SUPER POWER!",
                (190, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                (0, 255, 255),
                3
            )


        # ====================================================
        # DRAW PLAYER
        # ====================================================

        if (
            not hit_invincible
            or
            int(
                current_time *
                10
            )
            %
            2
            ==
            0
        ):

            cv2.rectangle(
                frame,
                (
                    int(player_left),
                    int(player_top)
                ),
                (
                    int(player_right),
                    int(player_bottom)
                ),
                (0, 255, 0),
                -1
            )


        # ====================================================
        # START SCREEN
        # ====================================================

        if not game_started:

            overlay = frame.copy()


            cv2.rectangle(
                overlay,
                (0, 0),
                (
                    WIDTH,
                    HEIGHT
                ),
                (0, 0, 0),
                -1
            )


            frame = cv2.addWeighted(
                overlay,
                0.72,
                frame,
                0.28,
                0
            )


            cv2.putText(
                frame,
                "HAND SURVIVOR",
                (145, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.4,
                (255, 255, 255),
                4
            )


            cv2.putText(
                frame,
                "Move your index finger to survive",
                (145, 195),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 220, 220),
                2
            )


            cv2.putText(
                frame,
                "FIST  =  START",
                (205, 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                3
            )


            cv2.putText(
                frame,
                "FIST  =  SUPER POWER",
                (170, 290),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                "OPEN HAND  =  PAUSE",
                (175, 320),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"HIGH SCORE: {high_score}",
                (230, 380),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 215, 255),
                2
            )


            cv2.putText(
                frame,
                "Q = QUIT",
                (270, 425),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 180, 180),
                2
            )


        # ====================================================
        # HUD
        # ====================================================

        if game_started:

            cv2.putText(
                frame,
                f"Score: {score}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Lives: {lives}",
                (15, 68),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Combo: x{combo}",
                (15, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Wave: {wave}",
                (15, 132),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Best: {high_score}",
                (15, 164),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2
            )


            # =================================================
            # SUPERPOWER STATUS
            # =================================================

            if super_power_active:

                power_text = (
                    "POWER: ACTIVE"
                )

            elif super_power_ready:

                power_text = (
                    "POWER: READY"
                )

            else:

                remaining = max(
                    0,
                    super_power_cooldown_until
                    -
                    current_time
                )


                power_text = (
                    f"POWER: {remaining:.1f}s"
                )


            cv2.putText(
                frame,
                power_text,
                (410, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )


            # =================================================
            # COMBO MESSAGE
            # =================================================

            if combo >= 5:

                cv2.putText(
                    frame,
                    f"COMBO x{combo}!",
                    (440, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )


            # =================================================
            # HIT MESSAGE
            # =================================================

            if (
                hit_invincible
                and
                not game_over
            ):

                cv2.putText(
                    frame,
                    "HIT!",
                    (285, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    3
                )


            # =================================================
            # WAVE MESSAGE
            # =================================================

            if (
                current_time
                <
                wave_message_until
            ):

                cv2.putText(
                    frame,
                    wave_message,
                    (225, 220),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.5,
                    (255, 255, 255),
                    4
                )


        # ====================================================
        # PAUSE SCREEN
        # ====================================================

        if (
            paused
            and
            not game_over
            and
            game_started
        ):

            overlay = frame.copy()


            cv2.rectangle(
                overlay,
                (0, 0),
                (
                    WIDTH,
                    HEIGHT
                ),
                (0, 0, 0),
                -1
            )


            frame = cv2.addWeighted(
                overlay,
                0.60,
                frame,
                0.40,
                0
            )


            cv2.putText(
                frame,
                "PAUSED",
                (225, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.6,
                (255, 255, 255),
                4
            )


            cv2.putText(
                frame,
                "OPEN HAND TO RESUME",
                (155, 275),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                "P = RESUME",
                (245, 320),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 180, 180),
                2
            )


        # ====================================================
        # GAME OVER
        # ====================================================

        if game_over:

            overlay = frame.copy()


            cv2.rectangle(
                overlay,
                (0, 0),
                (
                    WIDTH,
                    HEIGHT
                ),
                (0, 0, 0),
                -1
            )


            frame = cv2.addWeighted(
                overlay,
                0.60,
                frame,
                0.40,
                0
            )


            cv2.putText(
                frame,
                "GAME OVER",
                (165, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                4
            )


            cv2.putText(
                frame,
                f"FINAL SCORE: {score}",
                (185, 205),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"HIGH SCORE: {high_score}",
                (205, 245),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 215, 255),
                2
            )


            cv2.putText(
                frame,
                f"BEST COMBO: x{best_combo}",
                (200, 280),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                "Press R to restart",
                (190, 330),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                "FIST to restart",
                (225, 365),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.imshow(
            window_name,
            frame
        )


        # ====================================================
        # KEYBOARD
        # ====================================================

        key = (
            cv2.waitKey(1)
            &
            0xFF
        )


        # ====================================================
        # QUIT
        # ====================================================

        if key == ord("q"):

            break


        # ====================================================
        # KEYBOARD PAUSE
        # ====================================================

        if (
            key == ord("p")
            and
            game_started
            and
            not game_over
        ):

            paused = not paused


        # ====================================================
        # RESTART
        # ====================================================

        if (
            key == ord("r")
            and
            game_over
        ):

            reset_game()


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()