

function Overview() {
  return (
    <div className="flex w-full">
      <div className="flex gap-5 w-full p-5">
      <div className="flex flex-col w-1/4 gap-5">
        <div className="w-full h-3/4 rounded-4xl p-5 bg-white shadow-lg">
          Database Summary
        </div>
        <div className="w-full h-1/4 rounded-4xl p-5 bg-white shadow-lg">
          Database Summary
        </div>
      </div>
        <div className="w-3/4   rounded-4xl p-5 bg-white shadow-lg">
          Database Visualization
        </div>
      </div> 
    </div>
  )
}

export default Overview
