import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { Send, RefreshCw, Bot } from "lucide-react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [collectedSymptoms, setCollectedSymptoms] = useState([]);
  
  // Checklist State
  const [activeChecklist, setActiveChecklist] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [noneSelected, setNoneSelected] = useState(false); // Track "None" checkbox
  
  // Track which disease the bot is currently verifying (for Rule 2)
  const [lastTargetDisease, setLastTargetDisease] = useState(null);

  const chatEndRef = useRef(null);
  const scrollToBottom = () => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
  useEffect(scrollToBottom, [messages, loading, activeChecklist]);

  const handleSend = async () => {
    if (input.trim() === "" && selectedOptions.length === 0 && !noneSelected) return;

    const displayInput = input.trim() === "" ? (noneSelected ? "None of the above." : "Symptoms selected.") : input;
    const userMessage = { sender: "user", text: displayInput };
    setMessages((prev) => [...prev, userMessage]);
    
    const textToSend = input;
    const optionsToSend = [...selectedOptions];
    const noneToSend = noneSelected;
    
    // Clear UI
    setInput("");
    setSelectedOptions([]);
    setNoneSelected(false);
    setActiveChecklist([]); 
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          text: textToSend, 
          symptoms: collectedSymptoms,
          explicit_symptoms: optionsToSend,
          is_none_selected: noneToSend, // <--- Logic for Rule 2 "No Option"
          last_target_disease: lastTargetDisease // Pass back the context
        }),
      });

      const data = await response.json();

      if (data.symptoms) setCollectedSymptoms(data.symptoms);

      // Handle New Checklist
      let newChecklist = [];
      if (data.prediction_raw && data.prediction_raw.checklist) {
        newChecklist = data.prediction_raw.checklist;
        // Save the target disease if it exists (for the next turn)
        if (data.prediction_raw.target_disease) {
            setLastTargetDisease(data.prediction_raw.target_disease);
        }
      } else {
          setLastTargetDisease(null);
      }

      const botResponse = { 
        sender: "bot", 
        text: data.reply,
        checklist: newChecklist 
      };
      setMessages((prev) => [...prev, botResponse]);
      setActiveChecklist(newChecklist);

    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [...prev, { sender: "bot", text: "Error connecting to Backend." }]);
    }
    setLoading(false);
  };

  const handleCheckboxChange = (id) => {
    if (id === "NONE_OPTION") {
        // If "None" clicked, clear others and toggle None
        if (!noneSelected) {
            setSelectedOptions([]);
            setNoneSelected(true);
        } else {
            setNoneSelected(false);
        }
    } else {
        // If normal option clicked, Uncheck "None"
        setNoneSelected(false);
        setSelectedOptions((prev) => {
            if (prev.includes(id)) return prev.filter(item => item !== id);
            return [...prev, id];
        });
    }
  };

  const handleReset = async () => {
     setMessages([]);
     setCollectedSymptoms([]);
     setActiveChecklist([]);
     setSelectedOptions([]);
     setNoneSelected(false);
     setLastTargetDisease(null);
     await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "reset", symptoms: [] }),
     });
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      <div className="header-branding">Dr. AUST <span className="version-tag">1.1</span></div>
      <div className="chat-window">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <h1>Hello, User</h1>
            <p>Describe your symptoms to receive a specialist recommendation.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.sender}`}>
              {msg.sender === "bot" && <div className="avatar bot-avatar"><Bot size={24} /></div>}
              <div className="message-bubble-wrapper">
                <div className="message-bubble">
                  <span dangerouslySetInnerHTML={{ 
                    __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br/>') 
                  }} />
                </div>
                {msg.checklist && msg.checklist.length > 0 && index === messages.length - 1 && (
                  <div className="checklist-container">
                    {msg.checklist.map((item) => (
                      <label key={item.id} className="custom-checkbox">
                        <input 
                          type="checkbox" 
                          checked={selectedOptions.includes(item.id)}
                          onChange={() => handleCheckboxChange(item.id)}
                        />
                        <span className="checkmark"></span>
                        <span className="label-text">{item.definition}</span>
                      </label>
                    ))}
                    {/* RULE 2: THE "NONE" OPTION */}
                    <label className="custom-checkbox">
                        <input 
                          type="checkbox" 
                          checked={noneSelected}
                          onChange={() => handleCheckboxChange("NONE_OPTION")}
                        />
                        <span className="checkmark" style={{borderColor: '#d96570'}}></span>
                        <span className="label-text" style={{color: '#d96570'}}>None of the above</span>
                      </label>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message-row bot">
            <div className="avatar bot-avatar loading-animate"><Bot size={24} /></div>
            <div className="message-bubble loading-text">Dr. AUST is thinking...</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="input-area">
        <div className="input-wrapper">
          <button className="icon-btn" onClick={handleReset}><RefreshCw size={20} /></button>
          <input
            className="chat-input"
            placeholder={activeChecklist.length > 0 ? "Select options above..." : "Type symptoms here..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button className="icon-btn send-btn" onClick={handleSend}><Send size={20} /></button>
        </div>
        <p className="disclaimer-text">Dr. AUST can make mistakes, so double-check recommendations.</p>
      </div>
    </div>
  );
}

export default App;