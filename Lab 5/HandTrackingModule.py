import cv2
import mediapipe as mp
import time


class handDetector():

    def __init__(
        self,
        mode=False,
        maxHands=2,
        detectionCon=0.5,
        trackCon=0.5
    ):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands

        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            model_complexity=1,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )

        self.mpDraw = mp.solutions.drawing_utils
        self.results = None


    def findHands(self, img, draw=True):

        imgRGB = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB
        )

        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:

            for handLms in self.results.multi_hand_landmarks:

                if draw:

                    self.mpDraw.draw_landmarks(
                        img,
                        handLms,
                        self.mpHands.HAND_CONNECTIONS
                    )

        return img


    def findPosition(
        self,
        img,
        handNo=0,
        draw=True
    ):

        lmList = []

        if (
            self.results is not None
            and self.results.multi_hand_landmarks
        ):

            # Prevent index error if requested hand does not exist
            if handNo >= len(
                self.results.multi_hand_landmarks
            ):
                return lmList

            myHand = (
                self.results.multi_hand_landmarks[
                    handNo
                ]
            )

            for landmark_id, lm in enumerate(
                myHand.landmark
            ):

                h, w, c = img.shape

                cx = int(lm.x * w)
                cy = int(lm.y * h)

                lmList.append(
                    [landmark_id, cx, cy]
                )

                if draw:

                    cv2.circle(
                        img,
                        (cx, cy),
                        15,
                        (255, 0, 255),
                        cv2.FILLED
                    )

        return lmList


def main():

    pTime = 0

    # If your webcam is usually camera 0,
    # use 0 here.
    cap = cv2.VideoCapture(0)

    detector = handDetector(
        detectionCon=0.7
    )

    while True:

        success, img = cap.read()

        if not success:
            print("Could not read camera.")
            continue

        img = detector.findHands(img)

        lmList = detector.findPosition(img)

        if len(lmList) != 0:
            print(lmList[4])

        cTime = time.time()

        if cTime != pTime:
            fps = 1 / (cTime - pTime)
        else:
            fps = 0

        pTime = cTime

        cv2.putText(
            img,
            str(int(fps)),
            (10, 70),
            cv2.FONT_HERSHEY_PLAIN,
            3,
            (255, 0, 255),
            3
        )

        cv2.imshow(
            "Image",
            img
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()