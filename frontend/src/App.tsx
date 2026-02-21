import { Route, Routes } from "react-router-dom"
import Login from "./Login"
import Landing from "./Landing"

function App() {
  return (
    <Routes>
      <Route path='/' element={<Login />} />
      <Route path='/landing' element={<Landing />} />
    </Routes>
  )
}

export default App
