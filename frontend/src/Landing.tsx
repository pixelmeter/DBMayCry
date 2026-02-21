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
      <div className="h-screen w-full flex flex-col justify-center items-center overflow-hidden relative">

        <div className="absolute -inset-12.5 -z-10 blur-[35px] overflow-hidden">
          <img src="/fuchsia-bg.svg" className="w-full object-cover -scale-x-100" />
        </div>
        <div className="absolute inset-0 -z-10 bg-black/10" />

        <div className="flex flex-col w-6/7 h-6/7 rounded-2xl bg-white/30 p-3 backdrop-blur-2xl shadow-xl">
          <div className="flex p-5 gap-6 items-center bg-gray-50 shadow-md">
            <p className="text-2xl"><FaDatabase /></p>
            <p className="text-2xl font-bold"> DataBase Name</p>
            <p>|</p>
            <p className="text-xl">{activeInterface === "overview" ? "Overview" : "Chat"} </p>
            <FiRepeat onClick={switchInterface} />
          </div>
          <div className=" flex w-full h-full min-h-0">
          {activeInterface === "overview" ? <Overview /> : <ChatInterface/>}
          </div>
        </div>

        
      </div>
    </>
  )
}

export default Landing
