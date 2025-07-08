import React, { useState, useEffect, useRef } from "react";
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  IconButton,
  CircularProgress,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { styled } from "@mui/system";

// Styled components for better aesthetics
const ChatContainer = styled(Container)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  height: "80vh", // Adjust height as needed
  maxWidth: "800px",
  backgroundColor: "#f5f5f5",
  borderRadius: theme.shape.borderRadius,

  overflow: "hidden",
}));

const MessagesBox = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflowY: "auto",
  padding: theme.spacing(2),
  backgroundColor: "#e8eaf6", // Light blue background for messages
  borderBottom: `1px solid ${theme.palette.divider}`,
  "&::-webkit-scrollbar": {
    width: "8px",
  },
  "&::-webkit-scrollbar-thumb": {
    backgroundColor: "#9fa8da", // Darker blue for scrollbar
    borderRadius: "4px",
  },
}));

const MessageBubble = styled(Paper)(({ theme, sender }) => ({
  padding: theme.spacing(1.5),
  borderRadius: theme.shape.borderRadius * 2,
  marginBottom: theme.spacing(1),
  maxWidth: "70%",
  wordWrap: "break-word",
  backgroundColor: sender === "user" ? "#166AC5" : "#ffffff",
  color: sender === "user" ? "#ffffff" : "#333333",
  alignSelf: sender === "user" ? "flex-end" : "flex-start",
}));

const InputBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: "#ffffff",
  borderTop: `1px solid ${theme.palette.divider}`,
  display: "flex",
  alignItems: "center",
}));

const ChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const API_BASE_URL = "http://localhost:5000/api"; // Your Flask backend URL

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (input.trim() === "") return;

    const newMessage = { sender: "user", message: input };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInput("");
    setLoading(true);

    try {
      const chatHistoryForAPI = messages.map((msg) => ({
        sender: msg.sender === "user" ? "user" : "system", // Agent responses are 'system' for LLM context
        message: msg.message,
      }));

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input, history: chatHistoryForAPI }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "agent", message: data.response },
      ]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          sender: "agent",
          message: `Error: ${error.message}. Please try again or check backend.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ChatContainer>
      <Box
        sx={{
          p: 2,
          backgroundColor: "#176AC6",
          color: "white",
          borderTopLeftRadius: 8,
          borderTopRightRadius: 8,
        }}
      >
        <Typography variant="h5" component="div" align="center">
          Enterprise Supply Chain Agent
        </Typography>
      </Box>
      <MessagesBox>
        {messages.length === 0 && (
          <Typography
            variant="body1"
            color="textSecondary"
            align="center"
            sx={{ mt: 4 }}
          >
            Start a conversation with your Supply Chain Agent!
            <br />
            Try asking: "What's the current inventory?", "Show me recent
            orders", or "Run automation".
          </Typography>
        )}
        {messages.map((msg, index) => (
          <MessageBubble key={index} sender={msg.sender}>
            <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
              {msg.message}
            </Typography>
          </MessageBubble>
        ))}
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </MessagesBox>
      <InputBox>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !loading) {
              handleSendMessage();
            }
          }}
          sx={{
            mr: 1,
            borderRadius: "25px",
            "& fieldset": { borderRadius: "25px" },
          }}
          disabled={loading}
        />
        <IconButton
          onClick={handleSendMessage}
          disabled={loading}
          sx={{
            backgroundColor: "#176AC6",
            color: "white",
            "&:hover": {
              backgroundColor: "#303f9f",
            },
            borderRadius: "50%",
            p: 1.5,
          }}
        >
          <SendIcon />
        </IconButton>
      </InputBox>
    </ChatContainer>
  );
};

export default ChatApp;
