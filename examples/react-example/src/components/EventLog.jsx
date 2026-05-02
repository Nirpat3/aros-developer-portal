export default function EventLog({ events }) {
  return (
    <div className="event-log">
      {events.length === 0 ? (
        <p style={{color: '#999'}}>Waiting for events...</p>
      ) : (
        events.map((event, idx) => (
          <div key={idx} className="event">
            <strong>{event.eventName}</strong>
            {' '}
            <span style={{color: event.status === 'sent' ? '#28a745' : '#dc3545'}}>
              {event.status}
            </span>
            <br/>
            <small>{event.timestamp}</small>
          </div>
        ))
      )}
    </div>
  )
}
