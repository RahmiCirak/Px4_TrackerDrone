import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

# YOLOv8 modelinin yüklenmesi
model = YOLO('best.pt')

class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_subscriber')
        self.subscription_rgb = self.create_subscription(
            Image, 
            'camera', 
            self.listener_callback_rgb, 
            10)       
        self.subscription_depth = self.create_subscription(
            Image, 
            'depth_camera', 
            self.listener_callback_depth, 
            10)
        self.subscription_rgb
        self.subscription_depth

        self.br = CvBridge()
        self.target_x = None
        self.target_y = None
        self.depth_image = None
        
        # Publisher for sending movement commands
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.pub = self.create_publisher(Twist, '/px4_1/offboard_velocity_cmd', qos_profile)

    def listener_callback_rgb(self, data):
        self.get_logger().info('Receiving video frame')

        # ROS Image mesajını OpenCV görüntüsüne dönüştür
        current_frame = self.br.imgmsg_to_cv2(data, desired_encoding="bgr8")
        image = current_frame
        (height, width, _) = current_frame.shape

        # Calculate the center of the frame
        center_w = width / 2
        center_h = height / 2


        # Nesne Algılama
        results = model.predict(image)
        img = results[0].plot()  # Tahmin sonuçlarını içeren görüntüyü çiz

        # Tespit edilen nesnelerin koordinatlarını çıkar
        if results[0].boxes:  # Eğer tespit edilen kutular varsa
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0]  # xyxy koordinatlarını al
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                self.target_x = center_x
                self.target_y = center_y
                self.get_logger().info(f"Object detected at ({center_x}, {center_y})")

                # Takip mekanizmasını burada ekleyin
                self.track_object(center_x, center_y, center_w, center_h)

        # Sonuçları Göster
        cv2.imshow('Detected Frame', img)
        cv2.waitKey(1)
    
    def listener_callback_depth(self, data):
        self.get_logger().info('Receiving Depth video frame')
        # Convert the ROS Image message to OpenCV image
        self.depth_image = self.br.imgmsg_to_cv2(data, desired_encoding="passthrough")


    def track_object(self, x, y, center_w, center_h):
        if self.depth_image is None:
            self.get_logger().info("No depth image received yet.")
            return
        
        # Get the shape of the depth image
        height, width = self.depth_image.shape

        # Normalize x and y values to a range of -1 to 1
        norm_x = (x - center_w) / center_w
        norm_y = (y - center_h) / center_h

        # Clip the x and y values to the valid range
        x_clipped = max(0, min(int(x), width - 1))
        y_clipped = max(0, min(int(y), height - 1))

        # Get the depth value at the detected object's center
        depth_value = self.depth_image[y_clipped, x_clipped]
        self.get_logger().info(f"Depth value at ({x}, {y}) is {depth_value}")

        # Create Twist message
        twist = Twist()

        # Adjust the movement based on the normalized offset
        if norm_y < -0.1:  # Object is above the center
            twist.linear.z = 1.0
        elif norm_y < -0.05: 
            twist.linear.z = 0.5
        elif norm_y > 0.1: 
            twist.linear.z = -1.0        
        elif norm_y > 0.05:  # Object is below the center
            twist.linear.z = -0.5
        else:
            twist.linear.z = 0.0

        if norm_x < -0.1: 
            twist.linear.x = 1.0        
        elif norm_x < -0.05:  # Object is left of the center
            twist.linear.x = 0.5
        elif norm_x > 0.1: 
            twist.linear.x = -1.0       
        elif norm_x > 0.05:  # Object is right of the center
            twist.linear.x = -0.5
        else:
            twist.linear.x = 0.0


        # Move forward or backward based on depth value
        desired_distance = 2.0  # Desired distance from the object
        if depth_value > desired_distance + 1.0:
            twist.linear.y = 1.0  # Move forward
        elif depth_value < desired_distance - 1.0:
            twist.linear.y = -1.0 # Move backward
        else:
            twist.linear.y = 0.0

        # Publish the twist message
        self.pub.publish(twist)
        self.get_logger().info(f"Publishing twist message: linear.z = {twist.linear.z}, linear.y = {twist.linear.x}, linear.x = {twist.linear.y}")

def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()