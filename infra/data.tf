

data "aws_sqs_queue" "video_processed_queue" {
  name = "video-processed-event"
}
