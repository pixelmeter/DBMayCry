import { useState } from "react"
import { useNavigate } from "react-router-dom"

function Login() {

  const navigate = useNavigate()

  const [loginMode, setLoginMode] = useState<"URI" | "SQLITE_FILE">("URI")
  const [initDB, setInitDB] = useState<"init" | "loading" | "loaded">("init")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const switchLoginMode = () => {
    setLoginMode(prev => prev === "URI" ? "SQLITE_FILE" : "URI")
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setInitDB("loading")

    try {
      if (loginMode === "URI") {

        const uriInput = (e.target as HTMLFormElement)
          .querySelector<HTMLInputElement>("input[name='uri']")

        const uri = uriInput?.value

        await fetch("http://127.0.0.1:8000/api/connect/uri", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ uri })
        })

      } else {

        if (!selectedFile) {
          alert("Please select a SQLite file.")
          setInitDB("init")
          return
        }

        const formData = new FormData()
        formData.append("file", selectedFile)

        await fetch("http://127.0.0.1:8000/api/connect/sqlite", {
          method: "POST",
          body: formData
        })
      }

      setInitDB("loaded")
      navigate("/landing")

    } catch (err) {
      console.error(err)
      setInitDB("init")
    }
  }

  return (
    <div className="h-screen w-full flex justify-center items-center relative overflow-hidden">

      <div className="absolute -inset-12.5 -z-10 blur-[35px]">
        <img src="/fuchsia-bg.svg" className="w-full h-full object-cover" />
      </div>

      <div className="w-4/7 flex p-6 gap-2 bg-white/30 text-black rounded-bl-4xl rounded-tr-4xl justify-between items-center backdrop-blur-2xl shadow-xl">

        {initDB === "init" ? (
          <>
            <div className="flex w-full p-5 text-2xl justify-center">
              <p className="w-4/5 font-bold">
                Connect using a database URI or upload a SQLite file.
              </p>
            </div>

            <div className="flex flex-col w-2/3 py-18 px-5 bg-purple-800/40 rounded-4xl items-center gap-5 shadow-md">

              <div className="text-xl font-semibold">
                Welcome to DBMayCry
              </div>

              {/* URI FORM */}
              <form
                className={`flex flex-col gap-3 w-[85%] transition-all duration-500 ${loginMode === "URI" ? "opacity-100" : "hidden"}`}
                onSubmit={handleSubmit}
              >
                <div>
                  <p className="px-2 py-1">Database URI</p>
                  <input
                    name="uri"
                    placeholder="dialect://user:pass@host:port/db"
                    className="bg-gray-50 w-full rounded p-2 text-sm"
                  />
                </div>

                <button className="px-8 py-2 rounded-full bg-purple-900 text-white font-semibold self-center">
                  Connect
                </button>
              </form>

              {/* SQLITE FILE FORM */}
              <form
                className={`flex flex-col gap-3 w-[85%] transition-all duration-500 ${loginMode === "SQLITE_FILE" ? "opacity-100" : "hidden"}`}
                onSubmit={handleSubmit}
              >
                <div>
                  <p className="px-2 py-1">Upload SQLite File</p>
                  <input
                    type="file"
                    accept=".db,.sqlite"
                    onChange={handleFileChange}
                    className="bg-gray-50 w-full rounded p-2"
                  />
                </div>

                <button className="px-8 py-2 rounded-full bg-purple-900 text-white font-semibold self-center">
                  Upload & Connect
                </button>
              </form>

              <button
                onClick={switchLoginMode}
                className="p-2 px-3 rounded underline"
              >
                {loginMode === "URI"
                  ? "Use SQLite File Instead"
                  : "Use Database URI Instead"}
              </button>

            </div>
          </>
        ) : (
          <p className="text-xl font-semibold">
            Initializing Database...
          </p>
        )}

      </div>
    </div>
  )
}

export default Login