import React, { useEffect, useState, useRef } from "react";
import './App.css'
import axios from "axios";
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ReplayIcon from '@mui/icons-material/Replay';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import AddIcon from '@mui/icons-material/Add';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { Tooltip } from "@mui/material";
import BillyBassPFP from "../public/BillyBigMouthBassPFP.png";

type Chat = {
    logID: number,
    title: string,
    messages: string[]
}

function App() {

    const [userInput, setUserInput] = useState<string>("");

    const [isResponding, setIsResponding] = useState<boolean>(false);
    const [hasText, setHasText] = useState<boolean>(false);

    const [chatLog, setChatLog] = useState<string[]>([]);
    const chatLogRef = useRef<HTMLDivElement>(null);

    const [chatLogHistory, setChatLogHistory] = useState<Chat[]>([]);
    const chatLogHistoryRef = useRef<HTMLTableElement>(null);

    const [currentResponseCounter, setCurrentResponseCounter] = useState<number>(1);

    const [isContinuouslyListening, setIsContinuouslyListening] = useState<boolean>(false);
    const [isListeningOnce, setIsListeningOnce] = useState<boolean>(false);

    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
    const [isContinuouslySpeaking, setIsContinuouslySpeaking] = useState<boolean>(false);

    const [showMicMenu, setShowMicMenu] = useState<boolean>(false);
    const [showOptionsMenu, setShowOptionsMenu] = useState<boolean>(false);

    const [wakeWordDetected, setWakeWordDetected] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const [isPreviousConversation, setIsPreviousConversation] = useState<boolean>(false);

    const [chatIndex, setChatIndex] = useState<number>(-1);

    const [hoveredElementID, setHoveredElementID] = useState<number>(-1);
    const [clickedID, setClickedID] = useState<number>(-1);
    const [optionsMenuTitle, setOptionsMenuTitle] = useState<string>("");

    const [isHoveringPreviousConversation, setIsHoveringPreviousConversation] = useState<boolean>(false);
    const [isHoveringOptionsMenu, setIsHoveringOptionsMenu] = useState<boolean>(false);

    const clearHistory = async () => {
        await axios.get("http://127.0.0.1:5000/api/clear-history");
    }

    const retrieveChatLogNames = async () => {
        return await axios.get("http://127.0.0.1:5000/api/get-previous-conversations")
    }

    useEffect(() => {
        setChatLog(["Hello!", "Hi! I'm Billy the Big Mouth Bass! Ask me anything!"]);
        setCurrentResponseCounter(1);

        clearHistory()
            .then(() => {
                // No further action needed
            })
            .catch((error) => {
                console.error('Error clearing history:', error);
            });

        retrieveChatLogNames()
            .then((response) => {
                const { logIDs, titles, messages } = response.data;
                const formattedTitles = logIDs.map((logID: number, index: number) => ({
                    logID: logID,
                    title: titles[index],
                    messages: messages[index]
                }));
                setChatLogHistory(formattedTitles);
                setChatIndex(formattedTitles.length + 1);
            })
            .catch((error) => {
                console.error('Error retrieving previous conversations:', error);
            });

    }, []);

    useEffect(() => {
        if (chatLogHistoryRef.current) {
            chatLogHistoryRef.current.scrollTop = 0; // Scroll to top
        }
    }, []);

    useEffect(() => {
        // Scroll to the latest message in the chat log
        if (chatLogRef.current) {
            const {scrollHeight, clientHeight} = chatLogRef.current;
            chatLogRef.current.scrollTop = scrollHeight - clientHeight;
        }
    }, [chatLog]);

    const generateTitle = async (text: string[]) => {
        const title = await axios.post("http://127.0.0.1:5000/api/generate-title", { text })
        console.log(title.data["title"])
        return title.data["title"]
    };

    const closeSubmission = () => {
        setIsResponding(true);
    }
    const openSubmission = () => {
        setIsResponding(false);
    }

    const updateChatLogHistory = (logID: number, newMessages: string[]) => {
        setChatLogHistory(currentChatLogHistory => {
            return currentChatLogHistory.map(chat => {
                if (chat.logID === logID) {
                    return { ...chat, messages: [...chat.messages, ...newMessages] };
                }
                return chat;
            });
        });
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement> | React.FormEvent<HTMLTextAreaElement> | React.FormEvent<HTMLButtonElement>) => {
        event.preventDefault();
        if (userInput.trim() === "" || isResponding) return;

        const tempUserInput = userInput;
        setChatLog(currentChatLog => [...currentChatLog, userInput]);
        setUserInput("");
        setHasText(false);

        closeSubmission();
        const chatResponse = await axios.post("http://127.0.0.1:5000/api/response", { tempUserInput });
        const chatGPTResponse = chatResponse.data["response"][0];
        openSubmission();

        const newChatLog = [...chatLog, userInput, chatGPTResponse];
        const newMessages = [userInput, chatGPTResponse];

        setChatLog(currentChatLog => [...currentChatLog, chatGPTResponse]);
        setCurrentResponseCounter(currentResponseCounter => currentResponseCounter + 2);
        const logID = chatIndex;

        if (!isPreviousConversation) {
            const title = await generateTitle([tempUserInput, chatGPTResponse]);
            setChatLogHistory(currentChatLogHistory => [...currentChatLogHistory, {logID, title, messages: newChatLog}]);
            setIsPreviousConversation(true);
            await axios.post("http://127.0.0.1:5000/api/add-new-chat-log", { title, newChatLog })
        } else {
            await axios.post("http://127.0.0.1:5000/api/add-messages", { newMessages, logID })
            updateChatLogHistory(logID, newMessages);
        }

        if (isContinuouslySpeaking) {
            setIsSpeaking(() => true);
            await axios.post("http://127.0.0.1:5000/api/speak", { chatGPTResponse });
            setIsSpeaking(() => false);
        }
    };

    const handleContinuousSpeaking = async (event: React.MouseEvent<HTMLDivElement, MouseEvent> | React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        event.preventDefault();
        if (isContinuouslyListening) return;
        setIsContinuouslySpeaking(!isContinuouslySpeaking);
    };

    const handleContinuousListening = async (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
        event.preventDefault();
        if (isListeningOnce) return;

        setIsContinuouslyListening(!isContinuouslyListening);
        if (!isContinuouslyListening) {
            setIsContinuouslySpeaking(true);
        } else {
            setIsContinuouslySpeaking(false);
        }

        if (isContinuouslyListening) {
            await axios.get("http://127.0.0.1:5000/api/stop-continuous-listening");
        }
    };

    const triggerWakeWordAnimation = () => {
        setWakeWordDetected(true);
        setTimeout(() => {
            setWakeWordDetected(false);
        }, 2000); // Adjust the time as needed for animation
    }

    useEffect(() => {
        const fetchChatLog = async () => {
            if (isContinuouslyListening && !isLoading) {
                setIsLoading(true);
                try {
                    console.log("Here");
                    await axios.get("http://127.0.0.1:5000/api/start-continuous-listening");
                    triggerWakeWordAnimation();

                    const response = await axios.get("http://127.0.0.1:5000/api/respond-to-user");
                    const chatLogData = response.data["chat_log"];

                    if (chatLogData !== "") {
                        setChatLog(currentChatLog => [...currentChatLog, chatLogData[0], chatLogData[1]])
                        setWakeWordDetected(false);
                    }
                } catch (error) {
                    console.error("ERROR: " + error);
                } finally {
                    setIsLoading(false);
                }
            }
        };

        if (isContinuouslyListening) {
            fetchChatLog()
                .then(() => {
                    // No further action needed
                })
                .catch((error) => {
                    console.error('Error fetching chat log:', error);
                });
        }
    }, [isContinuouslyListening, isLoading, wakeWordDetected]);

    const handleListenOnce = async (event: { preventDefault: () => void; } | undefined) => {
        event && event.preventDefault();
        if (isListeningOnce || isContinuouslyListening) {
            return;
        }
        setIsListeningOnce(() => true) ;
        const response = await axios.get("http://127.0.0.1:5000/api/detect-speech")
        setUserInput(currentUserInput => currentUserInput + " " + response.data["speech"]);
        if (userInput + response.data["speech"].trim() === "") {
            setHasText(false);
        } else {
            setHasText(true);
        }
        setIsListeningOnce(() => false);
    }

    const handleUserInput = async (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const userInput = event.target.value;
        setUserInput(userInput);
        setHasText(userInput.length > 0)
    };

    const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSubmit(event)
                .then(() => {
                    // No further action needed
                })
                .catch((error) => {
                    console.error('Error submitting form:', error);
                });
        }
    };

    const handleSpeakChatResponse = async (event: React.MouseEvent<SVGSVGElement, MouseEvent>, chatGPTResponse: string) => {
        event.preventDefault();
        setIsSpeaking(() => true);
        await axios.post("http://127.0.0.1:5000/api/speak", { chatGPTResponse });
        setIsSpeaking(() => false);
    };

    const handleStopSpeaking = async (event: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
        event.preventDefault();
        setIsSpeaking(false);
        await axios.get("http://127.0.0.1:5000/api/stop-speaking");
    }

    const handleCopy = async (message : string) => {
        await navigator.clipboard.writeText(message);
    };

    const handleRegenerateResponse = async (event: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
        event?.preventDefault();
        const tempUserInput = chatLog[chatLog.length - 2];

        const newMessages = chatLog.slice(0, -1);
        setChatLog(currentChatLog => currentChatLog.slice(0, -1));

        const chatResponse = await axios.post("http://127.0.0.1:5000/api/response", { tempUserInput });
        const chatGPTResponse = chatResponse.data["response"][0];
        setChatLog(currentChatLog => [...currentChatLog, chatGPTResponse]);

        await axios.post("http://127.0.0.1:5000/api/reset-history", { newChatLog: chatLog });
        await axios.post("http://127.0.0.1:5000/api/add-messages", { newMessages, logID: chatIndex });

        if (isContinuouslySpeaking) {
            await axios.post("http://127.0.0.1:5000/api/speak", { chatGPTResponse });
        }
    };

    const handleNewChat = async () => {
        setChatLog(["Hello!", "Hi! I'm Billy the Big Mouth Bass! Ask me anything!"]);
        setUserInput("");
        setIsPreviousConversation(false);
        setChatIndex(chatLogHistory.length + 1);
        setCurrentResponseCounter(1);
        await axios.get("http://127.0.0.1:5000/api/clear-history");
    };

    const handleChangeChatLog = async (logID: number) => {
        if (logID === chatIndex || isHoveringOptionsMenu) return;

        setIsPreviousConversation(true);
        const chatLogData = await axios.post("http://127.0.0.1:5000/api/get-chat-log", { logID })

        const newChatLog = chatLogData.data['messages'];
        await axios.post("http://127.0.0.1:5000/api/reset-history", { newChatLog });
        setCurrentResponseCounter(newChatLog.length - 1);
        setChatLog(newChatLog);
        setChatIndex(logID);
    }

    const handleHoveringEnter = (logID: number) => {
        setIsHoveringPreviousConversation(true);
        setHoveredElementID(logID)
    }

    const handleHoveringLeave = () => {
        setIsHoveringPreviousConversation(false);
        setHoveredElementID(-1);
    }

    const handlePreviousResponseOptions = async (logID: number) => {
        setShowOptionsMenu(true);
        setClickedID(() => logID);
        const optionsTitle = await axios.post("http://127.0.0.1:5000/api/get-title", { logID });
        setOptionsMenuTitle(optionsTitle.data['title']);
    }

    const handlePageClick = () => {
        showMicMenu ? setShowMicMenu(false) : null;
    }

    const handleChangePersonality = async (event: React.ChangeEvent<HTMLSelectElement>) => {
        const personality: string = event.target.value;
        await axios.post("http://127.0.0.1:5000/api/change-personality", { personality });
    }

  return (
      <div
          className={'page-container'}
          onClick={handlePageClick}
      >
          <div
              className={'previous-response-box'}
          >
              <div
                  className={'new-chat-button'}
                  onClick={handleNewChat}
              >
                  <AddIcon sx={{color: '#8D5C22', fontSize: 25,}}/><p className={'new-chat-button-text'}>Start A New Chat</p>
              </div>
              <table className={'previous-response-title-container'} ref={chatLogHistoryRef}>
                  {chatLogHistory.map(({logID, title}) => (
                      <tr
                          key={logID}
                          onClick={() => handleChangeChatLog(logID)}
                      >
                          <td
                              className={'previous-response-title fade-text'}
                              style={{backgroundColor: isHoveringPreviousConversation || isHoveringOptionsMenu ?
                                      chatIndex === logID ? "#253022"
                                          :
                                      hoveredElementID === logID ? "#404d3e" : "inherit"
                                      :
                                      chatIndex === logID ? "#253022" : "inherit"
                              }}
                              onMouseOver={() => handleHoveringEnter(logID)}
                              onMouseLeave={() => handleHoveringLeave()}
                              onClick={() => setIsHoveringPreviousConversation(false)}
                          >{title + logID}
                              {chatIndex === logID &&
                              <div className={'previous-response-title-options-background'}
                                   style = {{backgroundColor: "#253022"}}
                              ></div>}
                              {hoveredElementID === logID && hoveredElementID !== chatIndex &&
                                  <div className={'previous-response-title-options-background'}
                                       style = {{backgroundColor: "#404d3e"}}
                                  ></div>}
                              {chatIndex === logID &&
                                  <MoreHorizIcon
                                  className={'previous-response-title-options'}
                                  onMouseOver={() => setIsHoveringOptionsMenu(true)}
                                  onMouseLeave={() => setIsHoveringOptionsMenu(false)}
                                  onClick={() => handlePreviousResponseOptions(logID)}/>}
                              {hoveredElementID === logID && hoveredElementID !== chatIndex &&
                                  <MoreHorizIcon
                                  className={'previous-response-title-options'}
                                  onMouseOver={() => setIsHoveringOptionsMenu(true)}
                                  onMouseLeave={() => setIsHoveringOptionsMenu(false)}
                                  onClick={() => handlePreviousResponseOptions(logID)}/>}
                          </td>
                          {showOptionsMenu && clickedID === logID && (
                              <div className={'options-menu'}>{optionsMenuTitle}</div>
                          )}
                      </tr>
                  ))}
              </table>
          </div>

          <div className={'response-box-container'}>
              <div className={'personality-modifier-selector-container'}>
                  <select
                      className={'personality-modifier-selector'}
                      id="personality-selector"
                      onChange={handleChangePersonality}
                  >
                      <option value="default">Default Billy</option>
                      <option value="insane">BAKA Billy</option>
                      <option value="academic">Academic Billy</option>
                  </select>
                  <span className="personality-modifier-chevron">👇</span>
              </div>
              <div className={'chat-log-container'} ref={chatLogRef}>
                  {chatLog.map((message, idx) => {

                      const isChatResponse = idx % 2 != 0;

                      return (
                          <div className={isChatResponse ? "chat-response" : "user-input"}>
                              {isChatResponse &&
                                  <img
                                      id="billyBass"
                                      src={BillyBassPFP}
                                      alt="Profile Picture"
                                      className={`profile-picture ${wakeWordDetected ? 'wiggle' : ''}`}
                                      onClick={() => triggerWakeWordAnimation()}
                                  />}
                              <p key={idx}>
                                  {message}
                                  {isChatResponse && (
                                      <div>
                                          <Tooltip title={isSpeaking ? "Stop Speaking" : "Speak Message"}>
                                              {isSpeaking ?
                                                  <MicOffIcon
                                                      sx={{fontSize: 20}}
                                                      className="buttons-under-chat-response"
                                                      onClick={(event) => handleStopSpeaking(event)}
                                                  />
                                                  :
                                                  <MicIcon
                                                      sx={{fontSize: 20}}
                                                      className="buttons-under-chat-response"
                                                      onClick={(event) => handleSpeakChatResponse(event, message)}
                                                  />}

                                          </Tooltip>
                                          <Tooltip title="Copy Message">
                                              <ContentCopyIcon
                                                  sx={{fontSize: 20}}
                                                  className="buttons-under-chat-response"
                                                  onClick={() => handleCopy(message)}
                                              />
                                          </Tooltip>
                                          {currentResponseCounter === idx && idx != 1 && (
                                              <Tooltip title="Regenerate Message">
                                                  <ReplayIcon
                                                      sx={{fontSize: 20}}
                                                      className="buttons-under-chat-response"
                                                      onClick={(event) => handleRegenerateResponse(event)}
                                                  />
                                              </Tooltip>)}
                                      </div>
                                  )}
                              </p>
                          </div>
                      );
                  })}
              </div>
              <form className={'text-submission-box'} id="form"
                    onSubmit={(event) => handleSubmit(event)}>
                  <div className={'mic-and-input-box'}>
                      <div className={'mic-button-container'}>
                          <button type="button" className={'mic-button'} onClick={() => setShowMicMenu(!showMicMenu)}>
                              <MicIcon/>
                          </button>
                          {showMicMenu && (
                              <div className="mic-menu" onClick={(event) => event.stopPropagation()}>
                                  <div
                                      className="mic-menu-item"
                                      onClick={(event) => handleContinuousSpeaking(event)}
                                  >Toggle Speaking <button
                                      className={'mic-menu-item-toggle'}
                                      style={{color: isContinuouslySpeaking ? "green" : "red"}}
                                  >{isContinuouslySpeaking ? "On" : "Off"}</button>
                                  </div>
                                  <div
                                      className="mic-menu-item"
                                      onClick={(event) => handleContinuousListening(event)}
                                  >Toggle Listening <button
                                      className={'mic-menu-item-toggle'}
                                      style={{color: isContinuouslyListening ? "green" : "red"}}
                                  >{isContinuouslyListening ? "On" : "Off"}</button>
                                  </div>
                                  <div
                                      className="mic-menu-item"
                                      onClick={!isListeningOnce || !isContinuouslyListening ? (event) => handleListenOnce(event) : () => null}
                                  >{isListeningOnce || isContinuouslyListening ? "Listening..." : "Listen Once"}
                                  </div>
                              </div>
                          )}
                      </div>
                      <textarea className={'text-box'} placeholder="Ask Billy" value={userInput} id="textarea"
                                dir="auto"
                                onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => handleUserInput(event)}
                                onSubmit={handleSubmit}
                                onKeyDown={handleKeyPress}
                      />
                  </div>
                  <div className={'submit-button-container'}>
                      <button
                          onClick={handleSubmit}
                          disabled={!hasText}
                          className={hasText || isResponding ? 'submit-button-enabled' : 'submit-button-disabled'}
                      >
                          {isResponding ?
                              <div className={'submit-button-responding-container'}>
                                  <div className={'dot'}/>
                                  <div className={'dot'}/>
                                  <div className={'dot'}/>
                              </div>
                              :
                              <ArrowUpwardIcon/>}
                      </button>
                  </div>
              </form>
          </div>
      </div>
  )
}

export default App;