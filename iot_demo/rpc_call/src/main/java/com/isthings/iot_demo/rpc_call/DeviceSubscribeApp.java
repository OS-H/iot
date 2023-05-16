package com.isthings.iot_demo.rpc_call;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

public class DeviceSubscribeApp {
    static MqttClient client;
    public static void main(String[] args) {
        String subTopic = "v1/devices/me/rpc/request/+";
        String pubTopic = "v1/devices/me/rpc/response/";
        String content = "ok";
        int qos = 2;
        String broker = "tcp://172.16.104.112:1883";
        String clientId = "test";
        String userName = "dss5XD0aWzPX6889bT1h";

        MemoryPersistence persistence = new MemoryPersistence();

        try {
            client = new MqttClient(broker, clientId, persistence);

            // MQTT 连接选项
            MqttConnectOptions connOpts = new MqttConnectOptions();
            connOpts.setUserName(userName);
            // 保留会话
            connOpts.setCleanSession(true);

            // 设置回调
            client.setCallback(new MqttCallback() {
                @Override
                public void connectionLost(Throwable throwable) {
                    System.out.println("连接断开，可以做重连");
                }

                @Override
                public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                    System.out.println("接收消息主题:" + topic);
                    System.out.println("接收消息内容:" + new String(mqttMessage.getPayload()));
                    String num = topic.split("v1/devices/me/rpc/request/")[1];
                    System.out.println("应答消息主题: " + (pubTopic+num));
                    client.publish(pubTopic+num, mqttMessage);
                }

                @Override
                public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {

                }
            });

            // 建立连接
            client.connect(connOpts);
            // 订阅
            client.subscribe(subTopic);
            System.out.println("连接broker成功: " + broker);

        } catch (MqttException me) {
            me.printStackTrace();
        }
    }
}
