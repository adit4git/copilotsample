using System;

namespace Integration.MQIntegration
{
    public class MqClient
    {
        public void SendMessage(string queueName, string payload)
        {
            Console.WriteLine($"Sending message to {queueName}: {payload}");
        }

        public string ReceiveMessage(string queueName)
        {
            Console.WriteLine($"Receiving message from {queueName}");
            return "{}";
        }
    }
}
