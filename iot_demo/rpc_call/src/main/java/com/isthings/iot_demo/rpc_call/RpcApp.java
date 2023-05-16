package com.isthings.iot_demo.rpc_call;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import org.apache.commons.codec.binary.StringUtils;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.util.EntityUtils;
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.io.IOException;

public class RpcApp {

    static String loginUri = "http://172.16.104.112/api/auth/login";
    static String rpc1Uri = "http://172.16.104.112/api/plugins/rpc/oneway/";
    static String rpc2Uri = "http://172.16.104.112/api/plugins/rpc/twoway/";
    static String devId = "368d6670-f2f1-11ed-8bcd-a33a4f608bef";

    public static void main(String[] args) {

        try {
            CloseableHttpClient httpClient = new DefaultHttpClient();
            HttpResponse httpResponse = null;
            String token = null;

            //1. login get token
            HttpPost httpPost = new HttpPost(loginUri);
            httpPost.setEntity(parseBody("{\"username\":\"admin@iot.com\",\"password\":\"12345\"}"));

            httpResponse = httpClient.execute(httpPost);
            if (httpResponse != null) {
                HttpEntity responseEntity = httpResponse.getEntity();
                if (responseEntity != null) {
                    JSONObject jsonObject = JSON.parseObject(EntityUtils.toString(responseEntity));
                    token = jsonObject.getString("token");
                }
            }
            if (token == null) {
                return;
            }
            System.out.println("login success");

            //2. rpc request
            httpPost = new HttpPost(rpc2Uri+ devId);
            httpPost.setEntity(parseBody("{\"method\":\"setTemp\",\"params\":\"100\"}"));
            httpPost.addHeader("X-Authorization", "Bearer "+token);
            httpResponse = httpClient.execute(httpPost);
            if (httpResponse != null) {
                HttpEntity responseEntity = httpResponse.getEntity();
                if (responseEntity != null) {
                    System.out.println("rpc request response:" + EntityUtils.toString(responseEntity));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static StringEntity parseBody(String data) throws Exception {
        StringEntity entity = new StringEntity(data,
                ContentType.APPLICATION_JSON.getMimeType(), "UTF-8");
        return entity;
    }
}
