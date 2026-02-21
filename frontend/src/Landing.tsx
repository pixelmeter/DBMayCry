import { useState } from "react"
import { FaDatabase } from "react-icons/fa"
import { FiRepeat } from "react-icons/fi"
import Overview from "./components/Overview"
import ChatInterface from "./components/ChatInterface"

function Landing() {
  const [activeInterface, setActiveInterface] = useState("overview")

  const switchInterface = () => {
    setActiveInterface(prev => prev === "overview" ? "chat" : "overview")
  }

  return (
    <>
      <div className="h-screen w-full flex flex-col justify-center items-center">
        <div className="flex flex-col w-6/7 h-6/7 rounded-4xl bg-gray-100">
          <div className="flex p-5 gap-6 items-center bg-gray-50">
            <p className="text-2xl"><FaDatabase /></p>
            <p className="text-2xl font-bold"> DataBase Name</p>
            <p>|</p>
            <p className="text-xl">{activeInterface === "overview" ? "Overview" : "Chat"} </p>
            <FiRepeat onClick={switchInterface} />
          </div>
          <div className=" flex w-full h-full ">
          {activeInterface === "overview" ? <Overview /> : <ChatInterface/>}
          </div>
        </div>

        
      </div>
    </>
  )
}

export default Landing
