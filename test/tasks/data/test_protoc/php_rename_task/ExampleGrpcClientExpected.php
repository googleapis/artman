<?php
namespace Google\Pubsub\V1;

class PublisherGrpcClient extends \Grpc\BaseStub {

    public function CreateTopic(\Google\Pubsub\V1\Topic $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/google.pubsub.v1.Publisher/CreateTopic',
        $argument,
        ['\Google\Pubsub\V1\Topic', 'decode'],
        $metadata, $options);
    }

    public function DeleteTopic(\Google\Pubsub\V1\DeleteTopicRequest $argument,
      $metadata = [], $options = []) {
        return $this->_simpleRequest('/google.pubsub.v1.Publisher/DeleteTopic',
        $argument,
        ['\Google\Protobuf\GPBEmpty', 'decode'],
        $metadata, $options);
    }
}
