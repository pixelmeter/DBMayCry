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
      <div className="h-screen w-full flex justify-center items-center">
        <div className="w-4/7 flex p-6 gap-2 bg-red-50 rounded-bl-4xl rounded-tr-4xl justify-between items-center">
          <div className="w-full p-5 text-2xl"> Lorem ipsum dolor sit, amet consectetur adipisicing elit. Incidunt labore modi molestias. Odio eos sapiente, sit porro dolores recusandae </div>
          <div className={`flex flex-col w-2/3 ${loginMode === "URI" ? "py-[10em]" : "py-[4em]"}  px-5 bg-red-100 rounded-4xl items-center gap-6`}>
            <div className=""> Welcome to DBMayCry </div>
            {loginMode === "URI" ? (
              <form className="flex flex-col gap-3 w-[85%]" onSubmit={handleSubmit}>
                <div className="w-full">
                  <p className="px-2 py-1">Database URI:</p>
                  <input type="text" name="" id="" className="bg-gray-50 w-full rounded py-1" />
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Database URI:</p>
                  <input type="text" name="" id="" className="bg-gray-50 w-full rounded py-1" />
                </div>
                <button className="px-3 py-1 rounded-full bg-blue-50">Submit</button>
              </form>
            ) : ( 
              <form className="flex flex-col gap-3 w-[85%]" onSubmit={handleSubmit}>
                <div className="w-full">
                  <p className="px-2 py-1">Host IP:</p>
                  <input placeholder="Host" className="bg-gray-50 w-full rounded p-1"/>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Port:</p>
                  <input placeholder="Port"  defaultValue={5432} className="bg-gray-50 w-full rounded p-1"/>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Database Name:</p>
                  <input placeholder="Database" className="bg-gray-50 w-full rounded p-1"/>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Username:</p>
                  <input placeholder="Username" className="bg-gray-50 w-full rounded p-1"/>
                </div>
                <div className="w-full">
                  <p className="px-2 py-1">Password:</p>
                  <input placeholder="Password" type="password" className="bg-gray-50 w-full rounded p-1"/>
                </div>
                <button className="px-3 py-1 rounded-full bg-blue-50">Submit</button>
              </form>
            )}

            <p>Or</p>

            <button onClick={switchLoginMode} className="bg-amber-100 p-2 px-3 rounded"> 
              Login With {loginMode === "URI" ? "Database Credentials" : "Database URI"}
            </button>

          </div>

        </div>
      </div>
    </>
  )
}

export default Login
