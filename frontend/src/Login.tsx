import { useState } from "react"
import { useNavigate } from "react-router-dom"

function Login() {

  const navigate = useNavigate()

  const [loginMode, setLoginMode] = useState("URI")

  const switchLoginMode = () => {
    setLoginMode(prev => prev === "URI" ? "Fields" : "URI")
    console.log(loginMode)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/landing')

  }

  return (
    <>
      <div className="h-screen w-full flex justify-center items-center relative">

        <div className="absolute -inset-12.5 -z-10 blur-[35px]">
          <img src="/fuchsia-bg.svg" className="w-full h-full object-cover" />
        </div>
        
        {/* Main Content */}
        <div className="w-4/7 flex p-6 gap-2 bg-white/30 text-black rounded-bl-4xl rounded-tr-4xl justify-between items-center backdrop-blur-2xl shadow-xl">
          <div className="flex w-full p-5 text-2xl justify-center">
            <p className="w-4/5 font-bold">
            Lorem ipsum dolor sit, amet consectetur adipisicing elit. Incidunt labore modi molestias. Odio eos sapiente, sit porro dolores recusandae 
            </p>
          </div>
          <div className={`flex flex-col w-2/3 py-18 px-5 bg-purple-800/40 rounded-4xl items-center gap-5 shadow-md transition-all`}>
            <div className="text-xl font-semibold"> Welcome to DBMayCry! </div>
            {/* URI Form */}
              <form
                className={`flex flex-col gap-3 w-[85%] overflow-hidden transition-all duration-500 ${loginMode === "URI" ? "max-h-125 opacity-100" : "max-h-0 opacity-0"}`}
                onSubmit={handleSubmit}
              >
                <div className="w-full">
                  <p className="px-2 py-1">Database URI:</p>
                  <input placeholder="dialect://user:passwd@host:port/dbname" className="bg-gray-50 w-full rounded p-2 text-sm"/>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Database Type:</p>
                  <select className="bg-gray-50 w-full rounded p-2 text-sm">
                    <option value="option1">PostgresSQL</option>
                    <option value="option1">SQLlite</option>
                    <option value="option1">MySQL</option>
                  </select>
                </div>
                <button className="px-8 py-2 rounded-full bg-purple-900 text-white  w-fit font-semibold self-center">Submit</button>
              </form>
              {/* Credentials Form */}
              <form
                className={`flex flex-col gap-3 w-[85%] overflow-hidden transition-all duration-500 ${loginMode === "Fields" ? "max-h-125 opacity-100" : "max-h-0 opacity-0"}`}
                onSubmit={handleSubmit}
              >
              <div className="flex gap-2">
                <div className="w-full">
                  <p className="px-2 py-1">Host IP:</p>
                  <input placeholder="Host" className="bg-gray-50 w-full rounded p-2"/>
                </div>
                  <div className="w-1/4">
                  <p className="px-2 py-1">Port:</p>
                <input placeholder="Port"  defaultValue={5432} className="bg-gray-50 w-full rounded p-2"/>
                </div>
              </div>
                <div className="w-full">
                  <p className="px-2 py-1">Database Name:</p>
                  <input placeholder="db_name" className="bg-gray-50 w-full rounded p-2"/>
                </div>
                <div className="flex gap-2">
                  <div className="w-full">
                    <p className="px-2 py-1">Username:</p>
                    <input placeholder="user" className="bg-gray-50 w-full rounded p-2"/>
                  </div>
                  <div className="w-full">
                    <p className="px-2 py-1">Password:</p>
                    <input placeholder="passwd" type="password" className="bg-gray-50 w-full rounded p-2"/>
                  </div>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Database Type:</p>
                  <select className="bg-gray-50 w-full rounded p-2 text-sm">
                    <option value="option1">PostgresSQL</option>
                    <option value="option1">SQLlite</option>
                    <option value="option1">MySQL</option>
                  </select>
                </div>
                <button className="px-8 py-2 rounded-full bg-purple-900 text-white  w-fit font-semibold self-center">Submit</button>
              </form>

            <p>Or</p>

            <button onClick={switchLoginMode} className="p-2 px-3 rounded underline"> 
              Login With {loginMode === "URI" ? "Database Credentials" : "Database URI"}
            </button>

          </div>

        </div>
      </div>
    </>
  )
}

export default Login
