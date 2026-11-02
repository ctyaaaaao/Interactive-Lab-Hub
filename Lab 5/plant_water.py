import cv2
import time
import json
import argparse
from datetime import datetime

import HandTrackingModule as htm


# ============================================================
# SETTINGS
# ============================================================

CAMERA_INDEX = 0

W_CAM = 640
H_CAM = 480

# Hold open palm this long to START / STOP.
GESTURE_HOLD_TIME = 1.0

# Ignore watering detection briefly after START,
# so the start gesture is not accidentally counted.
START_DELAY = 2.0

LOG_FILE = "plant_log.jsonl"

# Default plant ROI:
# [x1, y1, x2, y2]
#
# You can change this after selecting your real plant area.
DEFAULT_ROI = [350, 100, 630, 460]


# ============================================================
# COMMAND-LINE OPTIONS
# ============================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--headless",
    action="store_true",
    help="Run without opening an OpenCV window"
)

parser.add_argument(
    "--roi",
    type=str,
    default=None,
    help="Plant ROI as x1,y1,x2,y2"
)

args = parser.parse_args()


# ============================================================
# ROI
# ============================================================

roi = DEFAULT_ROI.copy()

if args.roi:
    try:
        values = [
            int(v)
            for v in args.roi.split(",")
        ]

        if len(values) == 4:
            roi = values
        else:
            raise ValueError

    except ValueError:
        print(
            "Invalid ROI. Use format:"
            " --roi x1,y1,x2,y2"
        )
        exit(1)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def write_log(event, **data):
    """
    Append one event to plant_log.jsonl.
    """

    record = {
        "time": timestamp(),
        "event": event,
        **data
    }

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(record)
            + "\n"
        )

    print(record)


def get_point(lm, landmark_id):
    """
    Return (x, y) for one hand landmark.
    """

    return (
        lm[landmark_id][1],
        lm[landmark_id][2]
    )


def point_inside_roi(
    point,
    roi_box
):
    """
    Is this point inside the plant area?
    """

    x, y = point
    x1, y1, x2, y2 = roi_box

    return (
        x1 <= x <= x2
        and y1 <= y <= y2
    )


def palm_center(lm):
    """
    Estimate center of palm.
    """

    landmark_ids = [
        0,
        5,
        9,
        13,
        17
    ]

    xs = []
    ys = []

    for landmark_id in landmark_ids:

        x, y = get_point(
            lm,
            landmark_id
        )

        xs.append(x)
        ys.append(y)

    return (
        int(sum(xs) / len(xs)),
        int(sum(ys) / len(ys))
    )


def hand_inside_roi(
    lm,
    roi_box
):
    """
    Consider the hand inside the plant area
    if the palm center or any fingertip
    enters the ROI.
    """

    points = [
        palm_center(lm),

        get_point(lm, 4),   # thumb
        get_point(lm, 8),   # index
        get_point(lm, 12),  # middle
        get_point(lm, 16),  # ring
        get_point(lm, 20)   # pinky
    ]

    for point in points:

        if point_inside_roi(
            point,
            roi_box
        ):
            return True

    return False


# ============================================================
# OPEN PALM DETECTION
# ============================================================

def is_open_palm(lm):
    """
    Open palm gesture.

    We check index, middle,
    ring and pinky.

    Thumb is ignored to make
    detection more reliable.
    """

    index_extended = (
        lm[8][2]
        < lm[6][2]
    )

    middle_extended = (
        lm[12][2]
        < lm[10][2]
    )

    ring_extended = (
        lm[16][2]
        < lm[14][2]
    )

    pinky_extended = (
        lm[20][2]
        < lm[18][2]
    )

    extended_count = sum([
        index_extended,
        middle_extended,
        ring_extended,
        pinky_extended
    ])

    # Allow one finger to be imperfect.
    return extended_count >= 3


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(
    CAMERA_INDEX
)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    W_CAM
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    H_CAM
)


if not cap.isOpened():
    print(
        "ERROR: Camera could not be opened."
    )
    exit(1)


# ============================================================
# HAND DETECTOR
# ============================================================

detector = htm.handDetector(
    detectionCon=0.7,
    trackCon=0.7
)


# ============================================================
# STATE
# ============================================================

state = "IDLE"

gesture_hold_start = None

# Prevent same open palm from
# causing START and STOP immediately.
gesture_armed = True

monitoring_start_time = None

# True while hand is currently
# inside the plant area.
hand_was_inside = False

p_time = 0


# ============================================================
# START MESSAGE
# ============================================================

print(
    "------------------------------------------"
)

print(
    "Plant Care Activity Watcher"
)

print(
    "------------------------------------------"
)

print(
    "Open palm = START / STOP"
)

print(
    "Hand enters plant area = WATERING"
)

print(
    f"Plant ROI = {roi}"
)

if not args.headless:

    print(
        "R = Select plant area"
    )

    print(
        "Q = Quit"
    )

else:

    print(
        "HEADLESS MODE"
    )

print(
    "------------------------------------------"
)


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        success, img = cap.read()

        if not success:

            print(
                "Could not read camera."
            )

            time.sleep(0.2)

            continue


        current_time = time.time()


        # ====================================================
        # HAND TRACKING
        # ====================================================

        img = detector.findHands(
            img,
            draw=not args.headless
        )

        lm_list = detector.findPosition(
            img,
            draw=False
        )


        # ====================================================
        # DRAW ROI
        # ====================================================

        if not args.headless:

            x1, y1, x2, y2 = roi

            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                img,
                "PLANT AREA",
                (
                    x1,
                    max(
                        20,
                        y1 - 10
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


        # ====================================================
        # HAND DETECTED
        # ====================================================

        if len(lm_list) != 0:

            center = palm_center(
                lm_list
            )

            palm_is_inside = (
                point_inside_roi(
                    center,
                    roi
                )
            )

            inside = hand_inside_roi(
                lm_list,
                roi
            )

            open_palm = is_open_palm(
                lm_list
            )


            if not args.headless:

                cv2.circle(
                    img,
                    center,
                    8,
                    (255, 0, 255),
                    cv2.FILLED
                )


            # ================================================
            # IDLE
            # ================================================

            if state == "IDLE":

                if not args.headless:

                    cv2.putText(
                        img,
                        f"Open palm: {open_palm}",
                        (30, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2
                    )


                # Start gesture should ideally
                # be outside the plant ROI.
                if (
                    open_palm
                    and gesture_armed
                    and not palm_is_inside
                ):

                    if gesture_hold_start is None:

                        gesture_hold_start = (
                            current_time
                        )


                    hold_duration = (
                        current_time
                        - gesture_hold_start
                    )


                    if not args.headless:

                        cv2.putText(
                            img,
                            (
                                f"Starting: "
                                f"{hold_duration:.1f}s"
                            ),
                            (30, 140),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 255),
                            2
                        )


                    if (
                        hold_duration
                        >= GESTURE_HOLD_TIME
                    ):

                        state = "MONITORING"

                        monitoring_start_time = (
                            current_time
                        )

                        write_log(
                            "monitoring_started"
                        )

                        print(
                            "Plant monitoring started."
                        )

                        gesture_hold_start = None

                        # Same open palm cannot
                        # immediately STOP.
                        gesture_armed = False

                else:

                    gesture_hold_start = None


            # ================================================
            # MONITORING
            # ================================================

            elif state == "MONITORING":

                # --------------------------------------------
                # RE-ARM START/STOP GESTURE
                # --------------------------------------------

                if not open_palm:

                    gesture_armed = True

                    gesture_hold_start = None


                # --------------------------------------------
                # STOP WITH OPEN PALM
                # --------------------------------------------

                # Open palm must be outside plant area
                # so watering interaction does not stop system.

                if (
                    open_palm
                    and gesture_armed
                    and not palm_is_inside
                ):

                    if gesture_hold_start is None:

                        gesture_hold_start = (
                            current_time
                        )


                    hold_duration = (
                        current_time
                        - gesture_hold_start
                    )


                    if not args.headless:

                        cv2.putText(
                            img,
                            (
                                f"Stopping: "
                                f"{hold_duration:.1f}s"
                            ),
                            (30, 140),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 0, 255),
                            2
                        )


                    if (
                        hold_duration
                        >= GESTURE_HOLD_TIME
                    ):

                        state = "FINISHED"

                        write_log(
                            "monitoring_stopped"
                        )

                        print(
                            "Plant monitoring stopped."
                        )

                        gesture_hold_start = None

                        gesture_armed = False


                # --------------------------------------------
                # WATERING DETECTION
                # --------------------------------------------

                else:

                    if (
                        monitoring_start_time
                        is not None
                        and
                        current_time
                        - monitoring_start_time
                        >= START_DELAY
                    ):

                        # Hand just entered plant ROI.
                        if (
                            inside
                            and
                            not hand_was_inside
                        ):

                            hand_was_inside = True

                            write_log(
                                "watering_detected"
                            )

                            print(
                                "Watering detected."
                            )


                        # Hand remains inside.
                        elif (
                            inside
                            and hand_was_inside
                        ):

                            if not args.headless:

                                cv2.putText(
                                    img,
                                    "WATERING DETECTED",
                                    (30, 150),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.8,
                                    (0, 0, 255),
                                    2
                                )


                        # Hand leaves plant ROI.
                        elif (
                            not inside
                            and hand_was_inside
                        ):

                            hand_was_inside = False

                            write_log(
                                "hand_left_plant_area"
                            )

                            print(
                                "Hand left plant area."
                            )


        # ====================================================
        # NO HAND DETECTED
        # ====================================================

        else:

            gesture_hold_start = None


            # Removing hand re-arms
            # the START/STOP gesture.
            if state == "MONITORING":

                gesture_armed = True


            # Hand disappeared while
            # previously inside ROI.
            if (
                state == "MONITORING"
                and hand_was_inside
            ):

                hand_was_inside = False

                write_log(
                    "hand_left_plant_area"
                )

                print(
                    "Hand left plant area."
                )


        # ====================================================
        # DISPLAY
        # ====================================================

        if not args.headless:

            if state == "IDLE":

                status_text = (
                    "Show OPEN PALM to start"
                )

                status_color = (
                    0,
                    255,
                    255
                )

            elif state == "MONITORING":

                status_text = (
                    "MONITORING PLANT"
                )

                status_color = (
                    0,
                    255,
                    0
                )

            else:

                status_text = (
                    "MONITORING FINISHED"
                )

                status_color = (
                    255,
                    0,
                    255
                )


            cv2.putText(
                img,
                status_text,
                (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                status_color,
                2
            )


            # FPS
            c_time = time.time()

            if p_time != 0:

                fps = (
                    1
                    / (
                        c_time
                        - p_time
                    )
                )

            else:

                fps = 0

            p_time = c_time


            cv2.putText(
                img,
                f"FPS: {int(fps)}",
                (500, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )


            cv2.imshow(
                "Plant Care Activity Watcher",
                img
            )


            key = (
                cv2.waitKey(1)
                & 0xFF
            )


            # ================================================
            # SELECT PLANT ROI
            # ================================================

            if key == ord("r"):

                selected = cv2.selectROI(
                    "Select Plant Area",
                    img,
                    fromCenter=False,
                    showCrosshair=True
                )

                x, y, w, h = selected


                if (
                    w > 0
                    and h > 0
                ):

                    roi = [
                        int(x),
                        int(y),
                        int(x + w),
                        int(y + h)
                    ]

                    print(
                        "Plant ROI selected:",
                        roi
                    )


                cv2.destroyWindow(
                    "Select Plant Area"
                )


            # ================================================
            # QUIT
            # ================================================

            if key == ord("q"):

                print(
                    "Exiting."
                )

                break


        # ====================================================
        # FINISHED STATE
        # ====================================================

        if state == "FINISHED":

            # Give GUI a moment to display result.
            if not args.headless:

                cv2.waitKey(500)

            break


finally:

    cap.release()

    if not args.headless:

        cv2.destroyAllWindows()

    print(
        "Plant Care Activity Watcher ended."
    )